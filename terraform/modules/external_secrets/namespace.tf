resource "kubernetes_namespace_v1" "external_secrets" {
  metadata {
    name = "external-secrets"
  }
}
