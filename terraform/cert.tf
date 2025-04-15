module "cert" {
  source     = "./modules/cert"
  depends_on = [module.external_secrets]
}
