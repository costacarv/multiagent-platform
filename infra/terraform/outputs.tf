output "cluster_name" {
  description = "Nome do cluster EKS criado"
  value       = module.eks.cluster_name
}

output "cluster_endpoint" {
  description = "Endpoint da API do Kubernetes"
  value       = module.eks.cluster_endpoint
}

output "ecr_repository_urls" {
  description = "URLs dos repositórios ECR para uso no Jenkins"
  value       = { for k, repo in aws_ecr_repository.app_repos : k => repo.repository_url }
}

output "configure_kubectl" {
  description = "Comando para conectar o kubectl local ao novo cluster EKS"
  value       = "aws eks update-kubeconfig --region ${var.aws_region} --name ${module.eks.cluster_name}"
}