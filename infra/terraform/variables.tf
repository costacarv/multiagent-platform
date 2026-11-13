variable "aws_region" {
  description = "Região AWS onde a infraestrutura será criada"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Ambiente de implantação"
  type        = string
  default     = "prod"
}

variable "cluster_name" {
  description = "Nome do cluster Amazon EKS"
  type        = string
  default     = "multiagent-eks-cluster"
}