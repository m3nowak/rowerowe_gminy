resource "helm_release" "traefik" {
  name       = "traefik"
  repository = "oci://ghcr.io/traefik/helm"
  chart      = "traefik"
  version    = "34.5.0"
  namespace  = one(kubernetes_namespace_v1.traefik.metadata).name
  wait       = false
  set {
    name  = "service.spec.externalTrafficPolicy"
    value = "Local"
  }
  set {
    name  = "providers.kubernetesCRD.allowExternalNameServices"
    value = true
  }
}
