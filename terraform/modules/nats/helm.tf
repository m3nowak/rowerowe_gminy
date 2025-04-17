resource "helm_release" "nats" {
  name       = "nats"
  namespace  = one(kubernetes_namespace_v1.nats.metadata).name
  chart      = "nats"
  repository = "https://nats-io.github.io/k8s/helm/charts/"
  version    = "1.2.8"
  values     = [file("${path.module}/values.yaml")]
}
