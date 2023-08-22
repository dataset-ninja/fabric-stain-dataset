Dataset **Fabric Stain Dataset** can be downloaded in [Supervisely format](https://developer.supervisely.com/api-references/supervisely-annotation-json-format):

 [Download](https://assets.supervisely.com/supervisely-supervisely-assets-public/teams_storage/w/S/rm/5yOLHf3gQ5sXhRcFm3VXlh0xkWpYaZXYn3FlrHumn9GlUOX03J6zsUsoYbp3lqhYqfnWNYqzMKPjMaZGKQ9Qrt85gZCD4LsXMY0PZV5Uqbl711NZDBNpwJ0AcS8p.tar)

As an alternative, it can be downloaded with *dataset-tools* package:
``` bash
pip install --upgrade dataset-tools
```

... using following python code:
``` python
import dataset_tools as dtools

dtools.download(dataset='Fabric Stain Dataset', dst_dir='~/dataset-ninja/')
```
Make sure not to overlook the [python code example](https://developer.supervisely.com/getting-started/python-sdk-tutorials/iterate-over-a-local-project) available on the Supervisely Developer Portal. It will give you a clear idea of how to effortlessly work with the downloaded dataset.

The data in original format can be [downloaded here](https://www.kaggle.com/datasets/priemshpathirana/fabric-stain-dataset/download?datasetVersionNumber=1).