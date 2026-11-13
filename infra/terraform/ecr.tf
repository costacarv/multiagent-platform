locals {
  ecr_repos = ["multiagent-api", "multiagent-frontend"]
}

resource "aws_ecr_repository" "app_repos" {
  for_each             = toset(local.ecr_repos)
  name                 = each.key
  image_tag_mutability = "MUTABLE"
  force_delete         = true

  image_scanning_configuration {
    scan_on_push = true # Habilita varredura nativa de vulnerabilidades no push
  }
}

resource "aws_ecr_lifecycle_policy" "cleanup_old_images" {
  for_each   = aws_ecr_repository.app_repos
  repository = each.value.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Mantém apenas as últimas 5 imagens para evitar custos de armazenamento"
        selection = {
          tagStatus   = "any"
          countType   = "imageCountMoreThan"
          countNumber = 5
        }
        action = {
          type = "expire"
        }
      }
    ]
  })
}