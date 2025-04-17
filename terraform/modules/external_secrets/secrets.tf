resource "kubernetes_secret_v1" "akeyless_secret_creds" {
  metadata {
    name      = "akeyless-secret-creds"
    namespace = kubernetes_namespace_v1.external_secrets.metadata[0].name
  }
  data = {
    accessId        = var.css_accessId
    accessType      = var.css_accessType
    accessTypeParam = var.css_accessTypeParam
  }
}
