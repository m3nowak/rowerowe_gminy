module "postgres" {
  source     = "./modules/postgres"
  depends_on = [module.external_secrets]
}
