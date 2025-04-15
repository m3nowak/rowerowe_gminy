resource "helm_release" "external_secrets" {
  name       = "external-secrets"
  repository = "https://charts.external-secrets.io/"
  chart      = "external-secrets"
  version    = "0.10.7"
  namespace  = kubernetes_namespace_v1.external_secrets.metadata[0].name
  wait       = false
}
