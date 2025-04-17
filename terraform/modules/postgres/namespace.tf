resource "kubernetes_namespace_v1" "postgres" {
  metadata {
    name = "postgres"
  }
}
