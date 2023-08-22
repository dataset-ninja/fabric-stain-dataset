import os
import shutil
from urllib.parse import unquote, urlparse

import numpy as np
import supervisely as sly
from dotenv import load_dotenv
from supervisely.io.fs import dir_exists, file_exists, get_file_name

import src.settings as s
from dataset_tools.convert import unpack_if_archive

# https://www.kaggle.com/datasets/priemshpathirana/fabric-stain-dataset


def download_dataset(teamfiles_dir: str) -> str:
    """Use it for large datasets to convert them on the instance"""
    api = sly.Api.from_env()
    team_id = sly.env.team_id()
    storage_dir = sly.app.get_data_dir()

    if isinstance(s.DOWNLOAD_ORIGINAL_URL, str):
        parsed_url = urlparse(s.DOWNLOAD_ORIGINAL_URL)
        file_name_with_ext = os.path.basename(parsed_url.path)
        file_name_with_ext = unquote(file_name_with_ext)

        sly.logger.info(f"Start unpacking archive '{file_name_with_ext}'...")
        local_path = os.path.join(storage_dir, file_name_with_ext)
        teamfiles_path = os.path.join(teamfiles_dir, file_name_with_ext)
        api.file.download(team_id, teamfiles_path, local_path)

        dataset_path = unpack_if_archive(local_path)

    if isinstance(s.DOWNLOAD_ORIGINAL_URL, dict):
        for file_name_with_ext, url in s.DOWNLOAD_ORIGINAL_URL.items():
            local_path = os.path.join(storage_dir, file_name_with_ext)
            teamfiles_path = os.path.join(teamfiles_dir, file_name_with_ext)

            if not os.path.exists(get_file_name(local_path)):
                api.file.download(team_id, teamfiles_path, local_path)

                sly.logger.info(f"Start unpacking archive '{file_name_with_ext}'...")
                unpack_if_archive(local_path)

            else:
                sly.logger.info(
                    f"Archive '{file_name_with_ext}' was already unpacked to '{os.path.join(storage_dir, get_file_name(file_name_with_ext))}'. Skipping..."
                )

        dataset_path = storage_dir
    return dataset_path


def convert_and_upload_supervisely_project(
    api: sly.Api, workspace_id: int, project_name: str
) -> sly.ProjectInfo:
    # project_name = "FABRIC STAIN DATASET"
    dataset_path = "APP_DATA/archive"
    batch_size = 30

    images_folder_name = "images"
    bboxes_folder_name = "annotations"
    bboxes_ext = ".txt"

    test = []

    def create_ann(image_path):
        labels = []

        image_np = sly.imaging.image.read(image_path)[:, :, 0]
        img_height = image_np.shape[0]
        img_wight = image_np.shape[1]

        bbox_name = get_file_name(image_path) + bboxes_ext

        bbox_path = os.path.join(curr_bboxes_path, bbox_name)
        if file_exists(bbox_path):
            with open(bbox_path) as f:
                content = f.read().split("\n")

                for curr_data in content:
                    if len(curr_data) != 0:
                        ann_data = list(map(float, curr_data.split(" ")))

                        left = int((ann_data[1] - ann_data[3] / 2) * img_wight)
                        right = int((ann_data[1] + ann_data[3] / 2) * img_wight)
                        top = int((ann_data[2] - ann_data[4] / 2) * img_height)
                        bottom = int((ann_data[2] + ann_data[4] / 2) * img_height)
                        rectangle = sly.Rectangle(top=top, left=left, bottom=bottom, right=right)
                        label = sly.Label(rectangle, obj_class)
                        labels.append(label)

            tag_name = image_path.split("/")[-2]
            tags = [sly.Tag(tag_meta) for tag_meta in tag_metas if tag_meta.name == tag_name]

            return sly.Annotation(img_size=(img_height, img_wight), labels=labels, img_tags=tags)

    obj_class = sly.ObjClass("stain", sly.Rectangle)
    tag_names = [
        "defect_free",
        "stain",
    ]
    tag_metas = [sly.TagMeta(name, sly.TagValueType.NONE) for name in tag_names]

    project = api.project.create(workspace_id, project_name, change_name_if_conflict=True)
    meta = sly.ProjectMeta(obj_classes=[obj_class], tag_metas=tag_metas)
    api.project.update_meta(project.id, meta.to_json())

    images_folder = os.path.join(dataset_path, images_folder_name)
    bboxes_folder = os.path.join(dataset_path, bboxes_folder_name)

    def count_jpg_files(folder_path):
        count = 0

        for root, _, files in os.walk(folder_path):
            for file in files:
                if file.lower().endswith(".jpg"):
                    count += 1

        return count

    progress = sly.Progress("Create dataset ds", count_jpg_files(images_folder))
    dataset = api.dataset.create(project.id, "ds", change_name_if_conflict=True)

    for curr_image_folder in os.listdir(images_folder):
        curr_images_path = os.path.join(images_folder, curr_image_folder)
        curr_bboxes_path = os.path.join(bboxes_folder, curr_image_folder)

        if dir_exists(curr_images_path):
            images_names = os.listdir(curr_images_path)

            for img_names_batch in sly.batched(images_names, batch_size=batch_size):
                images_pathes_batch = [
                    os.path.join(curr_images_path, image_name) for image_name in img_names_batch
                ]
                img_names_batch = [f"{curr_image_folder}_{name}" for name in img_names_batch]
                img_infos = api.image.upload_paths(dataset.id, img_names_batch, images_pathes_batch)
                img_ids = [im_info.id for im_info in img_infos]

                anns_batch = [create_ann(image_path) for image_path in images_pathes_batch]
                api.annotation.upload_anns(img_ids, anns_batch)

                progress.iters_done_report(len(img_names_batch))
    return project
