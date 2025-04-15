resource "kubernetes_manifest" "postgres" {
  for_each   = fileset(path.module, "manifests/*.yaml")
  depends_on = [kubernetes_namespace_v1.postgres]
  manifest   = yamldecode(file("${path.module}/${each.value}"))
}
