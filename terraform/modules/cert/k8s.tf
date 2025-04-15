resource "kubernetes_manifest" "ces" {
  manifest = yamldecode(file("${path.module}/manifests/ces.yaml"))
}
