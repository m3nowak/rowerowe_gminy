resource "kubernetes_manifest" "nats" {
  for_each   = fileset(path.module, "manifests/*.yaml")
  depends_on = [kubernetes_namespace_v1.nats]
  manifest   = yamldecode(file("${path.module}/${each.value}"))
}
