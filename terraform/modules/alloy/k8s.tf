resource "kubernetes_manifest" "alloy" {
  for_each   = fileset(path.module, "manifests/*.yaml")
  depends_on = [kubernetes_namespace_v1.alloy]
  manifest   = yamldecode(file("${path.module}/${each.value}"))
}
