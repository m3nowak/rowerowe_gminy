module "posthog" {
  source     = "./modules/posthog"
  depends_on = [module.cert, module.traefik]
}
