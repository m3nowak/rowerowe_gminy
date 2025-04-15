resource "kubernetes_namespace_v1" "posthog" {
  metadata {
    name = "posthog"
    labels = {
      spawn-cert = "cloudflare-cert"
    }
  }
}
