<#
.SYNOPSIS
    REST API Integration Demo - Weather and User API Calls
.DESCRIPTION
    Demonstrates how to call REST APIs using PowerShell
    Includes weather API and user management API examples
.DATE
    2026-02-13
#>

# Set UTF8 encoding
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# ============================================
# Function Definitions
# ============================================

function Get-WeatherInfo {
    param(
        [double]$Latitude = 39.9042,
        [double]$Longitude = 116.4074,
        [string]$CityName = "Beijing"
    )
    
    Write-Host "`n=== Weather Info [$CityName] ===" -ForegroundColor Cyan
    
    $apiUrl = "https://api.open-meteo.com/v1/forecast" +
              "?latitude=$Latitude" +
              "&longitude=$Longitude" +
              "&current_weather=true" +
              "&timezone=Asia/Shanghai"
    
    Write-Host "URL: $apiUrl" -ForegroundColor Gray
    
    try {
        $response = Invoke-RestMethod -Uri $apiUrl -ErrorAction Stop
        
        # Weather code lookup
        $weatherCodes = @{
            0  = "Clear sky"
            1  = "Mainly clear"
            2  = "Partly cloudy"
            3  = "Overcast"
            45 = "Fog"
            48 = "Depositing rime fog"
            51 = "Light drizzle"
            53 = "Moderate drizzle"
            55 = "Dense drizzle"
            61 = "Slight rain"
            63 = "Moderate rain"
            65 = "Heavy rain"
            71 = "Slight snow"
            73 = "Moderate snow"
            75 = "Heavy snow"
            95 = "Thunderstorm"
        }
        
        $weatherDesc = $weatherCodes[$response.current_weather.weathercode]
        if (-not $weatherDesc) { $weatherDesc = "Code: $($response.current_weather.weathercode)" }
        
        $dayNight = if ($response.current_weather.is_day -eq 1) { "Day" } else { "Night" }
        
        Write-Host "`nWeather Report:" -ForegroundColor Green
        Write-Host "  City: $CityName" -ForegroundColor Yellow
        Write-Host "  Condition: $weatherDesc" -ForegroundColor Yellow
        Write-Host "  Temperature: $($response.current_weather.temperature) C" -ForegroundColor Yellow
        Write-Host "  Wind Speed: $($response.current_weather.windspeed) km/h" -ForegroundColor Yellow
        Write-Host "  Wind Direction: $($response.current_weather.winddirection) degrees" -ForegroundColor Yellow
        Write-Host "  Time: $($response.current_weather.time)" -ForegroundColor Yellow
        
        return [PSCustomObject]@{
            City = $CityName
            Condition = $weatherDesc
            Temperature = "$($response.current_weather.temperature)C"
            WindSpeed = "$($response.current_weather.windspeed) km/h"
            WindDirection = "$($response.current_weather.winddirection)"
            DayNight = $dayNight
            Time = $response.current_weather.time
        }
    }
    catch {
        Write-Error "Failed to get weather: $_"
        return $null
    }
}

function Get-UserInfo {
    param([int]$UserId = 1)
    
    Write-Host "`n=== User Info [ID: $UserId] ===" -ForegroundColor Cyan
    
    $url = "https://jsonplaceholder.typicode.com/users/$UserId"
    
    try {
        $user = Invoke-RestMethod -Uri $url -ErrorAction Stop
        
        Write-Host "`nUser Details:" -ForegroundColor Green
        Write-Host "  ID: $($user.id)"
        Write-Host "  Name: $($user.name)"
        Write-Host "  Username: $($user.username)"
        Write-Host "  Email: $($user.email)"
        Write-Host "  Phone: $($user.phone)"
        Write-Host "  Website: $($user.website)"
        Write-Host "  Company: $($user.company.name)"
        Write-Host "  City: $($user.address.city)"
        
        return $user
    }
    catch {
        Write-Error "Failed to get user: $_"
        return $null
    }
}

function New-BlogPost {
    param(
        [Parameter(Mandatory=$true)]
        [string]$Title,
        
        [Parameter(Mandatory=$true)]
        [string]$Body,
        
        [int]$UserId = 1
    )
    
    Write-Host "`n=== Create New Post ===" -ForegroundColor Cyan
    
    $postData = @{
        title = $Title
        body = $Body
        userId = $UserId
    }
    
    $jsonBody = $postData | ConvertTo-Json
    
    Write-Host "Request Body: $jsonBody" -ForegroundColor Gray
    
    try {
        $result = Invoke-RestMethod `
            -Uri "https://jsonplaceholder.typicode.com/posts" `
            -Method POST `
            -ContentType "application/json" `
            -Body $jsonBody `
            -ErrorAction Stop
        
        Write-Host "`n[SUCCESS] Post Created!" -ForegroundColor Green
        Write-Host "  Post ID: $($result.id)" -ForegroundColor Green
        Write-Host "  Title: $($result.title)" -ForegroundColor Green
        Write-Host "  User ID: $($result.userId)" -ForegroundColor Green
        
        return $result
    }
    catch {
        Write-Error "Failed to create post: $_"
        return $null
    }
}

function Invoke-ApiDemo {
    Write-Host "`n========================================" -ForegroundColor Magenta
    Write-Host "     REST API Integration Demo" -ForegroundColor Magenta
    Write-Host "========================================" -ForegroundColor Magenta
    
    # 1. GET - Weather API
    $beijingWeather = Get-WeatherInfo -Latitude 39.9042 -Longitude 116.4074 -CityName "Beijing"
    
    # 2. GET - User API
    $user = Get-UserInfo -UserId 1
    
    # 3. POST - Create Post
    $newPost = New-BlogPost -Title "PowerShell REST API Tutorial" -Body "Today I learned how to call REST APIs using PowerShell, including GET and POST requests!" -UserId 1
    
    Write-Host "`n========================================" -ForegroundColor Magenta
    Write-Host "         Demo Completed!" -ForegroundColor Magenta
    Write-Host "========================================" -ForegroundColor Magenta
}

# ============================================
# Main Entry
# ============================================

if ($MyInvocation.InvocationName -eq $PSCommandPath -or $MyInvocation.InvocationName -like "*API_Demo*") {
    Invoke-ApiDemo
    
    Write-Host "`nTips: You can also call individual functions:" -ForegroundColor Cyan
    Write-Host '  Get-WeatherInfo -Latitude 31.2304 -Longitude 121.4737 -CityName "Shanghai"' -ForegroundColor Yellow
    Write-Host '  Get-UserInfo -UserId 2' -ForegroundColor Yellow
    Write-Host '  New-BlogPost -Title "My Title" -Body "My Content" -UserId 1' -ForegroundColor Yellow
}
