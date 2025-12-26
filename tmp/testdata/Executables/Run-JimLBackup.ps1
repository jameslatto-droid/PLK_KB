#Requires -Version 5.1
<#
.SYNOPSIS
    Backup script for JimL BitLocker-encrypted external drive.

.DESCRIPTION
    This script mirrors specified folders from D: drive to the external JimL drive
    and creates a compressed archive of the backup.
    
    The script is designed to run from the JimL drive itself and auto-detects
    its own drive letter at runtime.

.NOTES
    Author: Senior Windows Automation Engineer
    Date: November 23, 2025
    Version: 1.0
#>

# ============================================================================
# CONFIGURATION
# ============================================================================

# Expected volume label for the backup drive
$EXPECTED_VOLUME_LABEL = "JimL"

# Backup folder mappings: Source -> Destination folder name
# To add/modify backups, edit this hashtable:
# Key = Full source path on D: drive
# Value = Destination folder name (will be created under <BACKUP_DRIVE>\Backup\)
$BackupMappings = @{
    "D:\Downloads"      = "Downloads"
    "D:\Onedrive PLK"   = "PLK"
    "D:\Onedrive DCT"   = "DCT"
}

# Robocopy options
# /MIR = Mirror (copy all, delete extra files in destination)
# /R:3 = Retry 3 times on failed copies
# /W:5 = Wait 5 seconds between retries
# /NFL = No file list (less verbose)
# /NDL = No directory list (less verbose)
# /NP = No progress percentage (cleaner output)
# /MT:8 = Multi-threaded (8 threads for faster copies)
# /XF = Exclude files (OneDrive temp/lock files)
$RobocopyOptions = @("/MIR", "/R:3", "/W:5", "/NFL", "/NDL", "/NP", "/MT:8", "/XF", "*.tmp", "~$*", "desktop.ini", ".DS_Store", "Thumbs.db", ".*")

# ============================================================================
# FUNCTIONS
# ============================================================================

function Write-ColorMessage {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Color
}

function Write-Header {
    param([string]$Text)
    Write-Host ""
    Write-ColorMessage "============================================================================" "Cyan"
    Write-ColorMessage $Text "Cyan"
    Write-ColorMessage "============================================================================" "Cyan"
    Write-Host ""
}

function Write-Success {
    param([string]$Message)
    Write-ColorMessage "[SUCCESS] $Message" "Green"
}

function Write-Error {
    param([string]$Message)
    Write-ColorMessage "[ERROR] $Message" "Red"
}

function Write-Warning {
    param([string]$Message)
    Write-ColorMessage "[WARNING] $Message" "Yellow"
}

function Write-Info {
    param([string]$Message)
    Write-ColorMessage "[INFO] $Message" "White"
}

function Get-BackupDrive {
    <#
    .SYNOPSIS
        Detects the drive letter where this script is running from.
    #>
    
    Write-Info "Detecting backup drive location..."
    
    # Get the drive letter from the script's location
    $scriptDrive = Split-Path -Qualifier $PSScriptRoot
    
    if ([string]::IsNullOrEmpty($scriptDrive)) {
        Write-Error "Could not determine script drive location."
        return $null
    }
    
    Write-Info "Script is running from: $scriptDrive"
    
    # Get volume information
    try {
        $volume = Get-Volume -DriveLetter $scriptDrive.TrimEnd(':') -ErrorAction Stop
        
        if ($volume.FileSystemLabel -ne $EXPECTED_VOLUME_LABEL) {
            Write-Error "Drive $scriptDrive has volume label '$($volume.FileSystemLabel)' but expected '$EXPECTED_VOLUME_LABEL'."
            Write-Error "Please ensure you are running this script from the JimL drive."
            return $null
        }
        
        Write-Success "Confirmed volume label: $($volume.FileSystemLabel)"
        return $scriptDrive
        
    } catch {
        Write-Error "Could not read volume information for $scriptDrive"
        Write-Error $_.Exception.Message
        return $null
    }
}

function Test-DriveAccess {
    <#
    .SYNOPSIS
        Tests if the backup drive is accessible (unlocked from BitLocker).
    #>
    param([string]$DriveLetter)
    
    Write-Info "Testing drive access..."
    
    $backupRoot = Join-Path $DriveLetter "Backup"
    
    try {
        # Try to create the Backup folder if it doesn't exist
        if (-not (Test-Path $backupRoot)) {
            New-Item -Path $backupRoot -ItemType Directory -Force | Out-Null
            Write-Info "Created backup root folder: $backupRoot"
        }
        
        # Try to write a test file
        $testFile = Join-Path $backupRoot ".test_access"
        "test" | Out-File -FilePath $testFile -Force -ErrorAction Stop
        Remove-Item -Path $testFile -Force -ErrorAction SilentlyContinue
        
        Write-Success "Drive is accessible and writable."
        return $true
        
    } catch {
        Write-Error "Cannot access or write to $backupRoot"
        Write-Error "Is the JimL BitLocker volume unlocked?"
        Write-Error "Error: $($_.Exception.Message)"
        return $false
    }
}

function Test-SourceFolders {
    <#
    .SYNOPSIS
        Validates that all source folders exist.
    #>
    
    Write-Info "Validating source folders..."
    $allExist = $true
    
    foreach ($source in $BackupMappings.Keys) {
        if (Test-Path $source) {
            Write-Success "Found: $source"
        } else {
            Write-Warning "Source folder not found: $source"
            $allExist = $false
        }
    }
    
    return $allExist
}

function Invoke-FolderBackup {
    <#
    .SYNOPSIS
        Performs the robocopy backup for all configured folders.
    #>
    param([string]$BackupDrive)
    
    $backupRoot = Join-Path $BackupDrive "Backup"
    $failedBackups = @()
    
    foreach ($source in $BackupMappings.Keys) {
        $destFolderName = $BackupMappings[$source]
        $destination = Join-Path $backupRoot $destFolderName
        
        Write-Header "Backing up: $source -> $destination"
        
        # Check if source exists
        if (-not (Test-Path $source)) {
            Write-Warning "Skipping $source (folder does not exist)"
            continue
        }
        
        # Create destination folder if needed
        if (-not (Test-Path $destination)) {
            New-Item -Path $destination -ItemType Directory -Force | Out-Null
        }
        
        # Build robocopy command - quote paths that contain spaces
        $robocopyArgs = @("`"$source`"", "`"$destination`"") + $RobocopyOptions
        
        Write-Info "Running: robocopy `"$source`" `"$destination`" $($RobocopyOptions -join ' ')"
        
        # Execute robocopy
        $result = Start-Process -FilePath "robocopy.exe" -ArgumentList $robocopyArgs -Wait -PassThru -NoNewWindow
        
        # Robocopy exit codes:
        # 0 = No files copied (no errors)
        # 1 = Files copied successfully
        # 2 = Extra files or directories detected
        # 4 = Mismatched files or directories
        # 8+ = Errors occurred
        
        $exitCode = $result.ExitCode
        
        if ($exitCode -ge 8) {
            Write-Error "Robocopy failed with exit code: $exitCode"
            Write-Error "This indicates errors during the copy operation."
            $failedBackups += $source
        } elseif ($exitCode -eq 0) {
            Write-Success "No changes needed for $source"
        } else {
            Write-Success "Completed backup of $source (exit code: $exitCode)"
        }
    }
    
    return $failedBackups
}

function Invoke-BackupCompression {
    <#
    .SYNOPSIS
        Creates a compressed ZIP archive of the entire Backup folder.
    #>
    param([string]$BackupDrive)
    
    Write-Header "Creating compressed archive"
    
    $backupRoot = Join-Path $BackupDrive "Backup"
    $archivePath = Join-Path $backupRoot "Backup_Archive.zip"
    
    # Remove old archive if it exists
    if (Test-Path $archivePath) {
        Write-Info "Removing old archive: $archivePath"
        try {
            Remove-Item -Path $archivePath -Force -ErrorAction Stop
        } catch {
            Write-Error "Could not remove old archive: $($_.Exception.Message)"
            return $false
        }
    }
    
    # Get all items to compress (excluding the archive itself)
    $itemsToCompress = Get-ChildItem -Path $backupRoot | Where-Object { $_.Name -ne "Backup_Archive.zip" }
    
    if ($itemsToCompress.Count -eq 0) {
        Write-Warning "No items found to compress in $backupRoot"
        return $false
    }
    
    Write-Info "Compressing $($itemsToCompress.Count) items to: $archivePath"
    Write-Info "This may take several minutes depending on data size..."
    
    try {
        # Compress each item
        foreach ($item in $itemsToCompress) {
            Write-Info "  Adding: $($item.Name)"
            
            if (Test-Path $archivePath) {
                # Update existing archive
                Compress-Archive -Path $item.FullName -DestinationPath $archivePath -Update -ErrorAction Stop
            } else {
                # Create new archive
                Compress-Archive -Path $item.FullName -DestinationPath $archivePath -ErrorAction Stop
            }
        }
        
        $archiveSize = (Get-Item $archivePath).Length / 1MB
        Write-Success "Archive created successfully: $archivePath"
        Write-Success "Archive size: $([math]::Round($archiveSize, 2)) MB"
        return $true
        
    } catch {
        Write-Error "Compression failed: $($_.Exception.Message)"
        return $false
    }
}

# ============================================================================
# MAIN SCRIPT
# ============================================================================

# Clear screen for clean output
Clear-Host

Write-Header "JimL Backup Script - Version 1.0"

# Step 1: Detect and validate backup drive
$backupDrive = Get-BackupDrive
if (-not $backupDrive) {
    Write-Error "Could not detect or validate backup drive."
    Write-Host ""
    Write-Host "Press any key to exit..."
    $null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')
    exit 1
}

# Step 2: Test drive access
if (-not (Test-DriveAccess -DriveLetter $backupDrive)) {
    Write-Host ""
    Write-Host "Press any key to exit..."
    $null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')
    exit 1
}

# Step 3: Validate source folders
Write-Host ""
$sourcesValid = Test-SourceFolders

if (-not $sourcesValid) {
    Write-Warning "Some source folders are missing. Backup will continue with available folders."
}

# Step 4: Display summary and ask for confirmation
Write-Header "Backup Summary"
Write-Info "Backup Drive: $backupDrive (Volume: $EXPECTED_VOLUME_LABEL)"
Write-Info "Backup Root: $backupDrive\Backup"
Write-Host ""
Write-Info "The following folders will be backed up:"
foreach ($source in $BackupMappings.Keys) {
    $dest = $BackupMappings[$source]
    $exists = if (Test-Path $source) { "OK" } else { "MISSING" }
    Write-Host "  [$exists] $source -> $backupDrive\Backup\$dest"
}
Write-Host ""
Write-Info "After sync, a ZIP archive will be created: $backupDrive\Backup\Backup_Archive.zip"
Write-Host ""

# Ask for confirmation
Write-ColorMessage "Do you want to proceed with the backup? (Y/N): " "Yellow" -NoNewline
$confirmation = Read-Host

if ($confirmation -ne 'Y' -and $confirmation -ne 'y') {
    Write-Warning "Backup cancelled by user."
    Write-Host ""
    Write-Host "Press any key to exit..."
    $null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')
    exit 0
}

# Step 5: Perform backup
Write-Host ""
$failedBackups = Invoke-FolderBackup -BackupDrive $backupDrive

# Step 6: Compress backup
Write-Host ""
$compressionSuccess = Invoke-BackupCompression -BackupDrive $backupDrive

# Step 7: Display final summary
Write-Header "Backup Complete"

if ($failedBackups.Count -eq 0) {
    Write-Success "All folder backups completed successfully."
} else {
    Write-Warning "Some backups failed:"
    foreach ($failed in $failedBackups) {
        Write-Host "  - $failed" -ForegroundColor Yellow
    }
}

if ($compressionSuccess) {
    Write-Success "Archive creation completed successfully."
} else {
    Write-Warning "Archive creation had issues (see messages above)."
}

Write-Host ""
$exitCode = if ($failedBackups.Count -eq 0 -and $compressionSuccess) { 0 } else { 1 }

if ($exitCode -eq 0) {
    Write-ColorMessage "Backup finished with no errors!" "Green"
} else {
    Write-ColorMessage "Backup finished with some warnings or errors." "Yellow"
}

Write-Host ""
Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')

exit $exitCode
