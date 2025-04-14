resource "helm_release" "external_secrets" {
  name       = "external-secrets"
  repository = "https://charts.external-secrets.io/"
  chart      = "external-secrets"
  version    = "0.10.7"

}

variable "css_accessId" {
  type      = string
  sensitive = true
}
variable "css_accessType" {
  type      = string
  sensitive = true
}
variable "css_accessTypeParam" {
  type      = string
  sensitive = true
}

resource "kubernetes_secret_v1" "akeyless_secret_creds" {
  metadata {
    name      = "akeyless-secret-creds"
    namespace = helm_release.external_secrets.namespace
  }
  data = {
    accessId        = var.css_accessId
    accessType      = var.css_accessType
    accessTypeParam = var.css_accessTypeParam
  }
}


resource "kubernetes_manifest" "css" {
  depends_on = [kubernetes_secret_v1.akeyless_secret_creds]
  manifest   = yamldecode(file("${path.module}/external-secrets-manifests/css.yaml"))
}
