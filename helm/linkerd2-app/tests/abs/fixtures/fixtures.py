import pytest

from pykube import ConfigMap
from pytest_helm_charts.giantswarm_app_platform.app_catalog import AppCatalogFactoryFunc

from pytest_helm_charts.giantswarm_app_platform.custom_resources import AppCR
from pytest_helm_charts.utils import wait_for_namespaced_objects_condition

cni_app_version = "0.3.1-beta-68af46a45a03e1cfc304fa40a0022fb163edb2d3"

timeout = 120


def app_cr_obj(name, catalog_name, version, namespace_config_annotations={}, namespace_config_labels={}):
    return {
        "kind": "App",
        "apiVersion": "application.giantswarm.io/v1alpha1",
        "metadata": {
            "name": name,
            "namespace": "giantswarm",
            "labels": {
                "app-operator.giantswarm.io/version": "0.0.0"
            }
        },
        "spec": {
            "catalog": catalog_name,
            "kubeConfig": {
                "inCluster": True
            },
            "name": name,
            "namespace": name,
            "namespaceConfig": {
                "annotations": namespace_config_annotations,
                "labels": namespace_config_labels,
            },
            "version": version
        }
    }


@pytest.fixture(scope="module")
def catalogs(kube_cluster, app_catalog_factory: AppCatalogFactoryFunc):
    for catalog_name in ["giantswarm", "giantswarm-test"]:
        app_catalog_factory(catalog_name, f"https://giantswarm.github.io/{catalog_name}-catalog/")


@pytest.fixture(scope="module")
def cni_app_cr(kube_cluster, catalogs):
    cni_app_name = "linkerd2-cni-app"
    app = app_cr_obj(
        cni_app_name,
        "giantswarm-test",
        cni_app_version,
        namespace_config_annotations={"linkerd.io/inject": "disabled"},
        namespace_config_labels={
            "linkerd.io/cni-resource": "true",
            "config.linkerd.io/admission-webhooks": "disabled"
        }
    )
    app_obj = AppCR(kube_cluster.kube_client, app)
    app_obj.create()
    apps = wait_for_namespaced_objects_condition(
        kube_cluster.kube_client,
        AppCR,
        [cni_app_name],
        "giantswarm",
        _app_deployed,
        timeout,
        True
    )

    return apps[0]


def user_configmap(filepath):
    with open(filepath, 'r', encoding='utf-8') as valuesfile:
        values = valuesfile.read()

    return values


@pytest.fixture(scope="module")
def linkerd_app_cr(kube_cluster, chart_version):
    app_name = "linkerd2-app"
    app_cm_name = f"{app_name}-user-config"

    app_cm = {
        "apiVersion": "v1",
        "kind": "ConfigMap",
        "metadata": {"name": app_cm_name, "namespace": "giantswarm"},
        "data": {"values": user_configmap("test-values.yaml")}
    }
    app_cm_obj = ConfigMap(kube_cluster.kube_client, app_cm)
    app_cm_obj.create()

    app = app_cr_obj(
        app_name,
        "chartmuseum",
        chart_version,
        namespace_config_annotations={"linkerd.io/inject": "disabled"},
        namespace_config_labels={
            "linkerd.io/is-control-plane": "true",
            "config.linkerd.io/admission-webhooks": "disabled",
            "linkerd.io/control-plane-ns": app_name
        }
    )
    app["spec"]["userConfig"] = {
        "configMap": {"name": app_cm_name, "namespace": "giantswarm"}
    }

    app_obj = AppCR(kube_cluster.kube_client, app)
    app_obj.create()
    apps = wait_for_namespaced_objects_condition(
        kube_cluster.kube_client,
        AppCR,
        [app_name],
        "giantswarm",
        _app_deployed,
        timeout,
        True
    )

    return apps[0]


def _app_deployed(app: AppCR) -> bool:
    complete = (
            "status" in app.obj
            and "release" in app.obj["status"]
            and "appVersion" in app.obj["status"]
            and "status" in app.obj["status"]["release"]
            and app.obj["status"]["release"]["status"] == "deployed"
    )
    return complete