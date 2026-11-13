# Bitácora de despliegue – MiRitmo (Entregable 1)

Cada comando con su salida. Los secretos se omiten o aparecen como `***`.

## 1. Identidad de la sesión AWS

_2026-11-13 11:50_ · código de salida 0

```
> aws sts get-caller-identity --profile miritmo
{
    "UserId": "AROAULMOKKJQ4NMMXZO2L:94d80438-5021-70c9-8465-db1f91703d30",
    "Account": "299335570017",
    "Arn": "arn:aws:sts::299335570017:assumed-role/AccountFullAccessRole/94d80438-5021-70c9-8465-db1f91703d30"
}
```

## 2. Plan de la cuenta (Free Tier)

_2026-11-13 11:50_ · código de salida 0

```
> aws freetier get-account-plan-state --profile miritmo --region us-east-1
{
    "accountId": "299335570017",
    "accountPlanType": "FREE",
    "accountPlanStatus": "ACTIVE",
    "accountPlanRemainingCredits": {
        "amount": 100.0,
        "unit": "USD"
    },
    "accountPlanExpirationDate": "2027-05-13T14:33:30.809000+00:00"
}
```

## 3. Rol de la sesión

_2026-11-13 11:50_ · código de salida 0

```
> aws iam list-roles --profile miritmo --query Roles[?RoleName=='AccountFullAccessRole'].[RoleName,Path,Arn] --output text
AccountFullAccessRole	/managed/	arn:aws:iam::299335570017:role/managed/AccountFullAccessRole
```

## 4. Bloqueo de acceso público de S3 a nivel cuenta

_2026-11-13 11:50_ · código de salida 254

```
> aws s3control get-public-access-block --account-id 299335570017 --profile miritmo --region us-east-2
[stderr]

aws: [ERROR]: An error occurred (NoSuchPublicAccessBlockConfiguration) when calling the GetPublicAccessBlock operation: The public access block configuration was not found
```

## 5. Límites de Lambda en la cuenta

_2026-11-13 11:50_ · código de salida 0

```
> aws lambda get-account-settings --profile miritmo --region us-east-2 --query AccountLimit
{
    "TotalCodeSize": 322122547200,
    "CodeSizeUnzipped": 262144000,
    "CodeSizeZipped": 52428800,
    "ConcurrentExecutions": 400,
    "UnreservedConcurrentExecutions": 400
}
```

## 6. Simulador de políticas IAM: acciones del despliegue (sin crear recursos)

_2026-11-13 11:50_ · código de salida 0

```
> aws iam simulate-principal-policy --profile miritmo --policy-source-arn arn:aws:iam::299335570017:role/managed/AccountFullAccessRole --action-names s3:CreateBucket s3:PutBucketPublicAccessBlock s3:PutBucketPolicy s3:PutObject cloudfront:CreateOriginAccessControl cloudfront:CreateDistribution cloudfront:CreateInvalidation iam:CreateRole iam:AttachRolePolicy iam:PassRole lambda:CreateFunction lambda:CreateFunctionUrlConfig lambda:AddPermission lambda:UpdateFunctionConfiguration logs:FilterLogEvents --query EvaluationResults[].[EvalActionName,EvalDecision] --output text
s3:CreateBucket	explicitDeny
s3:PutBucketPublicAccessBlock	explicitDeny
s3:PutBucketPolicy	explicitDeny
s3:PutObject	explicitDeny
cloudfront:CreateOriginAccessControl	allowed
cloudfront:CreateDistribution	allowed
cloudfront:CreateInvalidation	allowed
iam:CreateRole	allowed
iam:AttachRolePolicy	allowed
iam:PassRole	allowed
lambda:CreateFunction	explicitDeny
lambda:CreateFunctionUrlConfig	explicitDeny
lambda:AddPermission	explicitDeny
lambda:UpdateFunctionConfiguration	explicitDeny
logs:FilterLogEvents	allowed
```

## 7. Simulador IAM con aws:RequestedRegion=us-east-2

_2026-11-13 11:50_ · código de salida 0

```
> aws iam simulate-principal-policy --profile miritmo --policy-source-arn arn:aws:iam::299335570017:role/managed/AccountFullAccessRole --action-names s3:CreateBucket s3:PutBucketPublicAccessBlock s3:PutBucketPolicy s3:PutObject lambda:CreateFunction lambda:CreateFunctionUrlConfig lambda:AddPermission lambda:UpdateFunctionConfiguration --context-entries ContextKeyName=aws:RequestedRegion,ContextKeyValues=us-east-2,ContextKeyType=string --query EvaluationResults[].[EvalActionName,EvalDecision,join(',',MatchedStatements[].SourcePolicyId)] --output text
s3:CreateBucket	allowed	AdministratorAccess
s3:PutBucketPublicAccessBlock	allowed	AdministratorAccess
s3:PutBucketPolicy	allowed	AdministratorAccess
s3:PutObject	allowed	AdministratorAccess
lambda:CreateFunction	allowed	AdministratorAccess
lambda:CreateFunctionUrlConfig	allowed	AdministratorAccess
lambda:AddPermission	allowed	AdministratorAccess
lambda:UpdateFunctionConfiguration	allowed	AdministratorAccess
```

## 8. IBM Cloud: cuenta y región seleccionadas (login --sso -r us-south hecho antes; código de un solo uso omitido)

_2026-11-13 11:55_ · código de salida 0

```
> C:\Users\aangu\AppData\Local\Microsoft\WinGet\Links\ibmcloud.exe target
API endpoint:      https://cloud.ibm.com
Region:            us-south
User:              andres.angulo@anahuac.mx
Account:           Andrés Angulo (f191d50cebbb4ec195285a71fedde14c) <-> 3224975
Resource group:    No resource group targeted, use 'C:\Users\aangu\AppData\Local\Microsoft\WinGet\Links\ibmcloud.exe target -g RESOURCE_GROUP'
CF API endpoint:   
Org:               
Space:
```

## 9. Instancia previa Cloudant-cr (Lite, au-syd, sin bases): borrar porque solo se permite una Lite por cuenta

_2026-11-13 11:55_ · código de salida 0

```
> C:\Users\aangu\AppData\Local\Microsoft\WinGet\Links\ibmcloud.exe resource service-instance-delete Cloudant-cr --recursive -f
Deleting service instance Cloudant-cr under account Andrés Angulo as andres.angulo@anahuac.mx...
OK
Service instance Cloudant-cr with ID crn:v1:bluemix:public:cloudantnosqldb:au-syd:a/f191d50cebbb4ec195285a71fedde14c:cfaec20f-4f60-41b7-86fb-bf732784a0d1:: is deleted successfully
```

## 10. Reclamaciones pendientes

_2026-11-13 11:55_ · código de salida 0

```
> C:\Users\aangu\AppData\Local\Microsoft\WinGet\Links\ibmcloud.exe resource reclamations
List all resource reclamations under account f191d50cebbb4ec195285a71fedde14c as andres.angulo@anahuac.mx...
OK

ID                                     Resource Instance ID                   Entity CRN                                                                                                               State       Target Time
a4431e27-847e-4e1f-b34b-ccba8de3de94   cfaec20f-4f60-41b7-86fb-bf732784a0d1   crn:v1:bluemix:public:cloudantnosqldb:au-syd:a/f191d50cebbb4ec195285a71fedde14c:cfaec20f-4f60-41b7-86fb-bf732784a0d1::   SCHEDULED   2026-11-20T17:55:29Z
```

## 11. Borrar de forma permanente la reclamación de Cloudant-cr

_2026-11-13 11:55_ · código de salida 0

```
> C:\Users\aangu\AppData\Local\Microsoft\WinGet\Links\ibmcloud.exe resource reclamation-delete a4431e27-847e-4e1f-b34b-ccba8de3de94 -f
Submitting request to delete resource reclamation a4431e27-847e-4e1f-b34b-ccba8de3de94 under account f191d50cebbb4ec195285a71fedde14c as andres.angulo@anahuac.mx...
OK
Request to delete reclamation a4431e27-847e-4e1f-b34b-ccba8de3de94 was submitted
```

## 12. Seleccionar grupo de recursos Default

_2026-11-13 11:55_ · código de salida 0

```
> C:\Users\aangu\AppData\Local\Microsoft\WinGet\Links\ibmcloud.exe target -g Default
Targeted resource group Default


                   
API endpoint:      https://cloud.ibm.com
Region:            us-south
User:              andres.angulo@anahuac.mx
Account:           Andrés Angulo (f191d50cebbb4ec195285a71fedde14c) <-> 3224975
Resource group:    Default
CF API endpoint:   
Org:               
Space:
```

## 13. Crear instancia miritmo-cloudant (plan lite, us-south, solo IAM)

_2026-11-13 11:55_ · código de salida 0

```
> C:\Users\aangu\AppData\Local\Microsoft\WinGet\Links\ibmcloud.exe resource service-instance-create miritmo-cloudant cloudantnosqldb lite us-south -p "{"legacyCredentials": false}"
Creating service instance miritmo-cloudant in resource group Default of account Andrés Angulo as andres.angulo@anahuac.mx...
OK
Service instance miritmo-cloudant was created.
                  
Name:             miritmo-cloudant
ID:               crn:v1:bluemix:public:cloudantnosqldb:us-south:a/f191d50cebbb4ec195285a71fedde14c:6dabef3a-2b91-42fe-9990-863c9ae57483::
GUID:             6dabef3a-2b91-42fe-9990-863c9ae57483
Location:         us-south
State:            provisioning
Type:             service_instance
Sub Type:         
Allow Cleanup:    false
Locked:           false
Created at:       2026-11-13T17:55:40Z
Updated at:       2026-11-13T17:55:48Z
Last Operation:             
                  Status    create in progress
                  Message   Started create instance operation
```

## 14. Instancia miritmo-cloudant activa

_2026-11-13 11:56_ · código de salida 0

```
> C:\Users\aangu\AppData\Local\Microsoft\WinGet\Links\ibmcloud.exe resource service-instance miritmo-cloudant
Retrieving service instance miritmo-cloudant in resource group Default under account Andrés Angulo as andres.angulo@anahuac.mx...
OK
                       
Name:                  miritmo-cloudant
ID:                    crn:v1:bluemix:public:cloudantnosqldb:us-south:a/f191d50cebbb4ec195285a71fedde14c:6dabef3a-2b91-42fe-9990-863c9ae57483::
GUID:                  6dabef3a-2b91-42fe-9990-863c9ae57483
Location:              us-south
Service Name:          cloudantnosqldb
Service Plan Name:     lite
Resource Group Name:   Default
State:                 active
Type:                  service_instance
Sub Type:              
Locked:                false
Created at:            2026-11-13T17:55:40Z
Created by:            andres.angulo@anahuac.mx
Updated at:            2026-11-13T17:56:06Z
Last Operation:                  
                       Status    create succeeded
                       Message   Provisioning is complete
```

## 15. Crear credencial de servicio con rol Manager

_2026-11-13 11:56_ · código de salida 0

```
> C:\Users\aangu\AppData\Local\Microsoft\WinGet\Links\ibmcloud.exe resource service-key-create miritmo-cloudant-cred Manager --instance-name miritmo-cloudant --output json
name: miritmo-cloudant-cred
state: active
role: None
crn: crn:v1:bluemix:public:cloudantnosqldb:us-south:a/f191d50cebbb4ec195285a71fedde14c:6dabef3a-2b91-42fe-9990-863c9ae57483:resource-key:b0bce5b8-36a7-438a-a64a-2c4e61e5772d
credentials.iam_role_crn: crn:v1:bluemix:public:iam::::serviceRole:Manager
(campos con credenciales omitidos)
```

## 16. Comprobar que la credencial es solo IAM (sin username/password heredados)

_2026-11-13 11:56_ · código de salida 0

```
> python -I C:\Users\aangu\AppData\Local\Temp\claude\044fda7bcf4101bb\d3bb958f-7955-4d83-a366-f179683b71d9\scratchpad\con_cloudant.py --campos
Campos de la credencial: apikey, host, iam_apikey_description, iam_apikey_id, iam_apikey_name, iam_role_crn, iam_serviceid_crn, url, username
```

## 17. Crear las bases usuarios y registros (credenciales pasadas por variables de entorno, no se muestran)

_2026-11-13 11:56_ · código de salida 0

```
> python -I C:\Users\aangu\AppData\Local\Temp\claude\044fda7bcf4101bb\d3bb958f-7955-4d83-a366-f179683b71d9\scratchpad\con_cloudant.py python -I "C:\Users\aangu\OneDrive\Documentos\Escuela\Anahuac\Semestre7\Cómputo en la Nube\MiRitmo\entregable-1\scripts\crear_bases_cloudant.py"
Base 'usuarios' creada.
  Base 'registros' creada.
```

## 18. S3: crear bucket privado en us-east-2

_2026-11-13 11:57_ · código de salida 0

```
> aws s3api create-bucket --bucket miritmo-frontend-5e016053 --region us-east-2 --create-bucket-configuration LocationConstraint=us-east-2 --profile miritmo
{
    "Location": "http://miritmo-frontend-5e016053.s3.amazonaws.com/",
    "BucketArn": "arn:aws:s3:::miritmo-frontend-5e016053"
}
```

## 19. S3: activar Bloquear todo el acceso público

_2026-11-13 11:57_ · código de salida 0

```
> aws s3api put-public-access-block --bucket miritmo-frontend-5e016053 --region us-east-2 --profile miritmo --public-access-block-configuration BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true

```

## 20. S3: comprobar bloqueo de acceso público

_2026-11-13 11:57_ · código de salida 0

```
> aws s3api get-public-access-block --bucket miritmo-frontend-5e016053 --region us-east-2 --profile miritmo
{
    "PublicAccessBlockConfiguration": {
        "BlockPublicAcls": true,
        "IgnorePublicAcls": true,
        "BlockPublicPolicy": true,
        "RestrictPublicBuckets": true
    }
}
```

## 21. S3: región del bucket

_2026-11-13 11:57_ · código de salida 0

```
> aws s3api get-bucket-location --bucket miritmo-frontend-5e016053 --region us-east-2 --profile miritmo
{
    "LocationConstraint": "us-east-2"
}
```

## 22. CloudFront: crear Origin Access Control

_2026-11-13 11:57_ · código de salida 0

```
> aws cloudfront create-origin-access-control --profile miritmo --region us-east-1 --origin-access-control-config "Name=miritmo-oac,Description=OAC de MiRitmo,SigningProtocol=sigv4,SigningBehavior=always,OriginAccessControlOriginType=s3" --query OriginAccessControl.{Id:Id,Name:OriginAccessControlConfig.Name,Firma:OriginAccessControlConfig.SigningBehavior}
{
    "Id": "E2LN3JMLIJCR54",
    "Name": "miritmo-oac",
    "Firma": "always"
}
```

## 23. CloudFront: crear distribución (origen S3 con OAC, redirect-to-https, index.html)

_2026-11-13 11:57_ · código de salida 0

```
> aws cloudfront create-distribution --profile miritmo --region us-east-1 --distribution-config file://evidencias/config/cloudfront.json --query Distribution.{Id:Id,ARN:ARN,Dominio:DomainName,Estado:Status}
{
    "Id": "E1C3936GEOWFBQ",
    "ARN": "arn:aws:cloudfront::299335570017:distribution/E1C3936GEOWFBQ",
    "Dominio": "dnfx295km7eni.cloudfront.net",
    "Estado": "InProgress"
}
```

## 24. S3: política del bucket (solo la distribución E1C3936GEOWFBQ puede leer)

_2026-11-13 11:57_ · código de salida 0

```
> aws s3api put-bucket-policy --bucket miritmo-frontend-5e016053 --region us-east-2 --profile miritmo --policy file://evidencias/config/politica-bucket.json

```

## 25. S3: estado de la política (no pública)

_2026-11-13 11:57_ · código de salida 0

```
> aws s3api get-bucket-policy-status --bucket miritmo-frontend-5e016053 --region us-east-2 --profile miritmo
{
    "PolicyStatus": {
        "IsPublic": false
    }
}
```

## 26. IAM: crear rol miritmo-lambda-rol (confianza: lambda.amazonaws.com de esta cuenta)

_2026-11-13 11:57_ · código de salida 0

```
> aws iam create-role --profile miritmo --role-name miritmo-lambda-rol --description "Rol de la Lambda de MiRitmo: solo CloudWatch Logs" --assume-role-policy-document file://evidencias/config/confianza-lambda.json --query Role.{Nombre:RoleName,ARN:Arn}
{
    "Nombre": "miritmo-lambda-rol",
    "ARN": "arn:aws:iam::299335570017:role/miritmo-lambda-rol"
}
```

## 27. IAM: adjuntar solo AWSLambdaBasicExecutionRole

_2026-11-13 11:57_ · código de salida 0

```
> aws iam attach-role-policy --profile miritmo --role-name miritmo-lambda-rol --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

```

## 28. IAM: políticas del rol

_2026-11-13 11:58_ · código de salida 0

```
> aws iam list-attached-role-policies --profile miritmo --role-name miritmo-lambda-rol
{
    "AttachedPolicies": [
        {
            "PolicyName": "AWSLambdaBasicExecutionRole",
            "PolicyArn": "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
        }
    ]
}
```

## 29. IAM: políticas en línea del rol (debe estar vacío)

_2026-11-13 11:58_ · código de salida 0

```
> aws iam list-role-policies --profile miritmo --role-name miritmo-lambda-rol
{
    "PolicyNames": []
}
```
