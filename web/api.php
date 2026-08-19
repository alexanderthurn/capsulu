<?php
/**
 * api.php — Lightweight Steam AppDetails Proxy for PHP Web Hosting (e.g. Feuerware)
 * Resolves dynamic Steam Store hashed header assets without CORS issues.
 */

header('Content-Type: application/json; charset=utf-8');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit;
}

$appid = isset($_GET['appid']) ? preg_replace('/[^0-9]/', '', $_GET['appid']) : null;

if (!$appid) {
    http_response_code(400);
    echo json_encode(['success' => false, 'error' => 'Missing appid parameter']);
    exit;
}

$steam_api_url = "https://store.steampowered.com/api/appdetails?appids=" . $appid;

$context = stream_context_create([
    'http' => [
        'timeout' => 6,
        'user_agent' => 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    ]
]);

$response = @file_get_contents($steam_api_url, false, $context);

if ($response === false) {
    // Try cURL fallback if allow_url_fopen is disabled
    if (function_exists('curl_init')) {
        $ch = curl_init();
        curl_setopt($ch, CURLOPT_URL, $steam_api_url);
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
        curl_setopt($ch, CURLOPT_TIMEOUT, 6);
        curl_setopt($ch, CURLOPT_USERAGENT, 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36');
        $response = curl_exec($ch);
        curl_close($ch);
    }
}

if (!$response) {
    http_response_code(502);
    echo json_encode(['success' => false, 'error' => 'Could not connect to Steam API']);
    exit;
}

$data = json_decode($response, true);
$app_data = isset($data[$appid]['data']) ? $data[$appid]['data'] : null;

if (!$app_data) {
    http_response_code(404);
    echo json_encode(['success' => false, 'error' => 'Game data not found on Steam']);
    exit;
}

$rel_info = isset($app_data['release_date']) ? $app_data['release_date'] : [];
$is_coming_soon = isset($rel_info['coming_soon']) && $rel_info['coming_soon'];
$rel_date = isset($rel_info['date']) ? $rel_info['date'] : '';

$price_str = 'Free';
if (!empty($app_data['is_free'])) {
    $price_str = 'Free to Play';
} elseif (!empty($app_data['price_overview']['final_formatted'])) {
    $price_str = $app_data['price_overview']['final_formatted'];
} elseif ($is_coming_soon) {
    $price_str = 'Coming Soon';
}

$genres = [];
if (!empty($app_data['genres'])) {
    foreach ($app_data['genres'] as $g) {
        if (!empty($g['description'])) {
            $genres[] = $g['description'];
        }
    }
}

echo json_encode([
    'success' => true,
    'appid' => (int)$appid,
    'name' => isset($app_data['name']) ? $app_data['name'] : 'Steam Game',
    'header_image' => isset($app_data['header_image']) ? $app_data['header_image'] : null,
    'capsule_image' => isset($app_data['capsule_image']) ? $app_data['capsule_image'] : null,
    'price' => $price_str,
    'is_coming_soon' => $is_coming_soon,
    'release_date' => $rel_date,
    'review_status' => $is_coming_soon ? 'Coming Soon' : 'Positive',
    'genres' => $genres
]);
