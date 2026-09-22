<?php
if (!defined('ABSPATH')) { exit; }
$slug = get_post_meta(get_queried_object_id(), '_sm_slug', true);
if (!$slug && is_page()) { $slug = get_post_field('post_name', get_queried_object_id()); }
if (is_404()) { $slug = '404'; }
if (!preg_match('/^[a-z0-9-]+$/', $slug ?: '')) { $slug = '404'; }
$file = get_template_directory() . '/shells/' . $slug . '.html';
if (!is_readable($file)) { $file = get_template_directory() . '/shells/about.html'; }
$html = file_get_contents($file);
$content = '';
if (!is_404() && have_posts()) {
    the_post();
    $content = apply_filters('the_content', get_the_content());
    $html = preg_replace('~<h1[^>]*>.*?</h1>~s', '<h1>' . esc_html(get_the_title()) . '</h1>', $html);
    // Preserve the designed home greeting.
    if ($slug === 'index') { $html = str_replace('<h1>Home</h1>', '<h1 class="hero__title">St. Monica&apos;s Parish</h1>', $html); }
} else {
    foreach (sm_page_data() as $page) { if ($page['slug'] === '404') { $content = $page['body']; } }
}
$html = str_replace('<!--PARISH_BODY-->', $content, $html);
$html = sm_urls($html);
$html = preg_replace('~<script src="[^"]*search-index\.js[^"]*"></script>~', sm_search_script(), $html);
ob_start(); wp_head(); $head = ob_get_clean();
ob_start(); wp_footer(); $footer = ob_get_clean();
ob_start(); wp_body_open(); $body_open = ob_get_clean();
$html = str_replace('</head>', $head . '</head>', $html);
$html = preg_replace('~(<body[^>]*>)~', '$1' . $body_open, $html, 1);
$html = str_replace('</body>', $footer . '</body>', $html);
echo $html; // Bundled templates plus WordPress-filtered page content; URLs escaped above.
