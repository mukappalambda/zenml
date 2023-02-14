---
description: How to manage MLFlow logged models and artifacts
---

The MLflow Model Registry is a [Model Registry](./model-registries.md) flavor
provided with the MLflow ZenML integration that uses
[the MLflow model registry service](https://mlflow.org/docs/latest/model-registry.html)
to manage and track ML models and their artifacts.

## When would you want to use it?

[MLflow Model Registry](https://mlflow.org/docs/latest/model-registry.html)) is
a powerful tool that you would typically use in the experimenting, QA and
production phase to manage and track machine learning model versions. It is
designed to help teams collaborate on model development and deployment, and keep
track of which models are being used in which environments. With MLflow Model
Registry, you can store and manage models, deploy them to different environments,
and track their performance over time. This tool is useful in the following
scenarios:

* If you are working on a machine learning project and want to keep track of
different model versions as they are developed and deployed.
* If you need to deploy machine learning models to different environments and
want to keep track of which version is being used in each environment.
* If you want to monitor and compare the performance of different model versions
over time, and make data-driven decisions about which models to use in production.
* If you want to simplify the process of deploying models either to a production
environment or to a staging environment for testing.

## How do you deploy it?

The MLflow Experiment Tracker flavor is provided by the MLflow ZenML
integration, you need to install it on your local machine to be able to register
an MLflow Model Registry component. Note that MLFlow model registry requires
[MLFlow Experiment Tracker](../experiment-trackers/mlflow.md) to be present in
the stack.

```shell
zenml integration install mlflow -y
```

Once the MLflow integration is installed, you can register an MLflow Model
Registry component in your stack:

```shell
# Register the MLflow model registry
zenml model-registry register mlflow_model_registry --flavor=mlflow

# Register and set a stack with the new model registry
zenml stack register custom_stack -r mlflow_model_registry ... --set
```

{% hint style="info" %}
The MLFlow Model Registry will automatically use the same configuration as the
MLFlow Experiment Tracker. So if you have a remote MLFlow tracking server
configured in your stack, the MLFlow Model Registry will also use the same
configuration.
{% endhint %}

## How do you use it?


### Built-in MLflow Model Registry step

After registering the MLflow Model Registry component in your stack, you can
use it in a pipeline by using the `mlflow_model_registry_step` which is a
built-in step that is provided by the MLflow ZenML integration. This step
automatically register the model that was produced by the previous step in the
pipeline.

```python
# Pipeline run with MLflow model registry step
mlflow_training_pipeline(
    importer=loader_mnist(),
    normalizer=normalizer(),
    trainer=tf_trainer(params=TrainerParameters(epochs=5, lr=0.003)),
    evaluator=tf_evaluator(),
    model_register=mlflow_register_model_step(
        params=MLFlowRegistryParameters(
            name="Tensorflow-mnist-model",
            description="A simple mnist model trained with zenml",
            tags={"framework": "tensorflow", "dataset": "mnist"},
            version_description=f"A run of the mlflow_training_pipeline with a learning rate of 0.0003",
        )
    ),
).run()
```

### ZenML Command line interface (CLI)

Sometimes adding a step to your pipeline is not the best option for you, as it
will register the model in the MLflow Model Registry every time you run the
pipeline. In this case, you can use the ZenML CLI to register your model
manually. The CLI provides a command called `zenml model-registry models register-version`
that you can use to register your model in the MLflow Model Registry.

```shell
zenml model-registry models register-version Tensorflow-model \
    --model-uri="file:///.../mlruns/667102566783201219/3973eabc151c41e6ab98baeb20c5323b/artifacts/model" \
    --tags key1 value1 --tags key2 value2 \
    --description="A new version of the tensorflow model with accuracy 98.88%" \
    --zenml-pipeline-name="mlflow_training_pipeline"
```

### List of available parameters

To register a model version in the MLflow Model Registry, you need to provide
list of parameters. when you use the built-in step, most of the parameters are
automatically filled in for you. However, you can still override them if you
want to. The following table shows the list of available parameters.

* `name`: The name of the model. This is a required parameter.
* `description`: A description of the registered model.
* `tags`: A list of tags to associate with the registered model.
* `model_uri`: The path to the model. This is a required parameter.
* `version_description`: A description of the model version.
* `version_tags`: A list of tags to associate with the model version.
* `zenml_pipeline_name`: The name of the ZenML pipeline that produced the model.
* `zenml_pipeline_run_id`: The run id of the ZenML pipeline that produced the
model.
* `zenml_pipeline_step_name`: The time when the ZenML pipeline that produced the
model was run.

{% hint style="info" %}
The `model_uri` parameter is the path to the model within the MLflow tracking
server. If you are using a local MLflow tracking server, the path will be
something like `file:///.../mlruns/667102566783201219/3973eabc151c41e6ab98baeb20c5323b/artifacts/model`.
If you are using a remote MLflow tracking server, the path will be something
like `s3://.../mlruns/667102566783201219/3973eabc151c41e6ab98baeb20c5323b/artifacts/model`.

You can find the path of the model in the MLflow UI. Go to the `Artifacts` tab
of the run that produced the model and click on the model. The path will be
displayed in the URL.

![MLflow UI](../../assets/mlflow/mlflow_ui_uri.png)
{% endhint %}

Check out the
[API docs](https://apidocs.zenml.io/latest/integration_code_docs/integrations-mlflow/#zenml.integrations.mlflow.model_registry.MLFlowModelRegistry)
You can also check out our examples pages for working examples that use the
MLflow Model Registry Example:

- [Manage Models with MLflow](https://github.com/zenml-io/zenml/tree/main/examples/mlflow_registry)