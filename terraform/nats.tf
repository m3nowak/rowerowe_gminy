module "nats" {
  source     = "./modules/nats"
  depends_on = [module.cert, module.traefik]
}
