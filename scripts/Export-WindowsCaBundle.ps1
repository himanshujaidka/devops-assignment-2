param(
    [Parameter(Mandatory = $true)]
    [string]$OutputPath
)

$ErrorActionPreference = 'Stop'
$certificates = @{}
foreach ($location in @('CurrentUser', 'LocalMachine')) {
    foreach ($name in @('Root', 'CA')) {
        $store = [System.Security.Cryptography.X509Certificates.X509Store]::new(
            $name, $location
        )
        try {
            $store.Open([System.Security.Cryptography.X509Certificates.OpenFlags]::ReadOnly)
            foreach ($certificate in $store.Certificates) {
                $certificates[$certificate.Thumbprint] = $certificate.RawData
            }
        }
        finally {
            $store.Close()
        }
    }
}

if ($certificates.Count -eq 0) {
    throw 'No CA certificates were found in the Windows certificate stores.'
}

$bundle = foreach ($rawData in $certificates.Values) {
    '-----BEGIN CERTIFICATE-----'
    [Convert]::ToBase64String($rawData, [Base64FormattingOptions]::InsertLineBreaks)
    '-----END CERTIFICATE-----'
}
[System.IO.File]::WriteAllLines(
    [System.IO.Path]::GetFullPath($OutputPath),
    [string[]]$bundle,
    [System.Text.Encoding]::ASCII
)
Write-Output "Exported $($certificates.Count) public CA certificates to $OutputPath"
