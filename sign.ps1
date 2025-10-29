# === ПАРАМЕТРЫ ===
$Dist = "D:\4096\dist"                           # где лежат exe
$Subject = "CN=Cropper4096 Developer"            # имя издателя
$Timestamp = $null                               # можно $null (без времени) или, например: "http://timestamp.comodoca.com/authenticode"

# === 1) Создаём самоподписанный сертификат для кода ===
$cert = New-SelfSignedCertificate `
  -Type CodeSigningCert `
  -Subject $Subject `
  -CertStoreLocation "Cert:\CurrentUser\My" `
  -KeyExportPolicy Exportable `
  -KeyAlgorithm RSA -KeyLength 2048 `
  -HashAlgorithm SHA256

Write-Host "Создан сертификат:" $cert.Thumbprint

# === 2) Делаем его доверенным на ЭТОЙ машине (для текущего пользователя) ===
# 2.1 Trusted Publishers
$storeTP = New-Object System.Security.Cryptography.X509Certificates.X509Store("TrustedPublisher","CurrentUser")
$storeTP.Open([System.Security.Cryptography.X509Certificates.OpenFlags]::ReadWrite)
$storeTP.Add($cert)
$storeTP.Close()

# 2.2 Trusted Root Certification Authorities
$storeRoot = New-Object System.Security.Cryptography.X509Certificates.X509Store("Root","CurrentUser")
$storeRoot.Open([System.Security.Cryptography.X509Certificates.OpenFlags]::ReadWrite)
$storeRoot.Add($cert)
$storeRoot.Close()

Write-Host "Сертификат добавлен в TrustedPublisher и Root (CurrentUser)."

# === 3) Подписываем все EXE в папке ===
Get-ChildItem -Path $Dist -Filter *.exe -ErrorAction Stop | ForEach-Object {
    Write-Host "Подписываю:" $_.FullName
    if ($Timestamp) {
        $sig = Set-AuthenticodeSignature -FilePath $_.FullName -Certificate $cert -TimestampServer $Timestamp
    } else {
        $sig = Set-AuthenticodeSignature -FilePath $_.FullName -Certificate $cert
    }
    # Покажем реальный статус и сообщение проверки
    $check = Get-AuthenticodeSignature -FilePath $_.FullName
    Write-Host "Статус:" $check.Status "—" $check.StatusMessage
}

Write-Host "Готово. Проверь подпись в Свойствах файла → Цифровые подписи."
