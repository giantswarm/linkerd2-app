[![CircleCI](https://circleci.com/gh/giantswarm/linkerd2-app.svg?style=shield)](https://circleci.com/gh/giantswarm/linkerd2-app)

# linkerd2-app chart

This chart is based on the official linkerd2 helm chart.

## Requirements

- you can install only one release of this chart per kubernetes cluster.
- it is strongly suggested to use the [`linkerd2-cni-app`](https://github.com/giantswarm/linkerd2-cni-app) as this results in a more secure setup.
  - the CNI must be installed before this chart, and `global.cniEnabled: true` must be set.
- with linkerd CNI enabled, all pods meshed by linkerd require a `PodSecurityPolicy`, which allows use of `EmptyDir` volumes
  - the injected linkerd-proxy container requires an `EmptyDir` volumes

## Installation

### Dependencies

This application requires the [`linkerd2-cni-app`](https://github.com/giantswarm/linkerd2-cni-app)
application to be already deployed in the cluster. This can be installed from the Giant Swarm
App Catalog via the Happa UI.

### Deployment

This chart diverges from the upstream chart slightly by taking the namespace value from Helm
directly, rather than from the values file. When installing through the Giant Swarm App platform, we recommend
to install via App CR. Make sure you set the required annotations and labels through the `spec.namespaceConfig`.

```yaml
...
  namespaceConfig:
    annotations:
      linkerd.io/inject: disabled
    labels:
      linkerd.io/is-control-plane: "true"
      config.linkerd.io/admission-webhooks: disabled
      linkerd.io/control-plane-ns: linkerd2-app
...
```

#### Deployment using helm

When using helm, the namespace must be created _before_
this chart is deployed. Assuming a namespace `linkerd` already exists, this chart can be
deployed with the following command:

```text
helm install --namespace linkerd -n linkerd giantswarm-playground-catalog/linkerd2-app
```

Make sure to add the neccessary annotations and labels to your namespace. Check out file [helm/linkerd2-app/templates/namespace.yaml](helm/linkerd2-app/templates/namespace.yaml) as example.

## Configuration

We've set `global.cniEnabled: true`, so if you're planning to install this chart
without the CNI plugin, you'll need to disable this also in your values.

Make sure you align the `global.namespace` value with the namespace you're planning to install this
app to.

### Note:

`values.yaml` uses [YAML anchors](https://helm.sh/docs/chart_template_guide/yaml_techniques/#yaml-anchors) to
be DRY where possible, however this can cause problems when these values are overridden by a custom
values file. If you wish to enabled or disable deployment of the `grafana` and `tracing` subcharts
then you should override the values at `.$subchart.enabled`, **not** `.global.$subchart.enabled`.

## Usage with `linkerd` cli

You can use the `linkerd` cli as usual with this app, be sure to specify the right namespace using the `--linkerd-namespace` flag.

## Compatibility

Tested on Giant Swarm release 10.1.0 on AWS with Kubernetes 1.15.5.

## Credit

* https://helm.linkerd.io/stable
