resource "kubernetes_manifest" "css" {
  depends_on = [kubernetes_secret_v1.akeyless_secret_creds, helm_release.external_secrets]
  manifest   = yamldecode(file("${path.module}/manifests/css.yaml"))
}
