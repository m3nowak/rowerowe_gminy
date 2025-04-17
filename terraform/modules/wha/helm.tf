resource "helm_release" "wha" {
  name      = "wha"
  chart     = "${path.module}/chart"
  namespace = one(kubernetes_namespace_v1.wha.metadata).name
  wait      = false
  set {
    name  = "generation"
    value = var.generation
  }
  set {
    name  = "clientId"
    value = var.client_id
  }
  set {
    name  = "imageVersion"
    value = var.image_version
  }

}
