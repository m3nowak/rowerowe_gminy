resource "helm_release" "postgres" {
  name       = "postgres"
  namespace  = one(kubernetes_namespace_v1.postgres.metadata).name
  chart      = "postgresql"
  repository = "oci://registry-1.docker.io/bitnamicharts/"
  version    = "16.3.4"
  values     = [file("${path.module}/values.yaml")]
}
