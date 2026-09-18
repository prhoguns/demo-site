<?php
if (!defined('ABSPATH')) { exit; }

function sc_page_data() {
    return json_decode(file_get_contents(get_template_directory() . '/pages.json'), true) ?: array();
}

// Bundle assets locally, and resolve pages with WordPress permalinks (including subdirectories).
function sc_url($path) {
    if (strpos($path, '/assets/') === 0 || strpos($path, '/wp-content/uploads/') === 0) {
        return get_template_directory_uri() . '/site' . $path;
    }
    $parts = wp_parse_url($path);
    $slug = trim($parts['path'] ?? '/', '/');
    $ids = get_option('sc_page_ids', array());
    $id = $ids[$slug === '' ? 'index' : $slug] ?? 0;
    $url = $id ? get_permalink($id) : home_url($parts['path'] ?? '/');
    if (!empty($parts['query'])) { $url .= (strpos($url, '?') === false ? '?' : '&') . $parts['query']; }
    if (!empty($parts['fragment'])) { $url .= '#' . $parts['fragment']; }
    return $url;
}
function sc_urls($html) {
    // WordPress block closing markers contain paths such as `/wp:paragraph`.
    // Leave those markers intact while converting public root-relative URLs.
    return preg_replace_callback('~(?<=["\x27(\s])/(?!/|wp:)[^"\x27\s<>),]+~u', function ($match) {
        return esc_url(sc_url(html_entity_decode($match[0], ENT_QUOTES, 'UTF-8')));
    }, $html);
}

function sc_setup_pages() {
    if (get_option('sc_installed_version')) { return; }
    $ids = array();
    $created = array();
    foreach (sc_page_data() as $page) {
        if ($page['slug'] === '404') { continue; }
        $slug = $page['slug'] === 'index' ? 'home' : $page['slug'];
        $existing = get_page_by_path($slug, OBJECT, 'page');
        if ($existing) { $ids[$page['slug']] = $existing->ID; continue; }
        $id = wp_insert_post(array('post_type' => 'page', 'post_status' => 'publish',
            'post_title' => $page['title'], 'post_name' => $slug, 'post_content' => '',
            'meta_input' => array('_sc_slug' => $page['slug'])), true);
        if (!is_wp_error($id)) { $ids[$page['slug']] = $id; $created[$page['slug']] = $page; }
    }
    update_option('sc_page_ids', $ids);
    foreach ($created as $slug => $page) {
        wp_update_post(array('ID' => $ids[$slug], 'post_content' => sc_urls($page['blocks'])));
    }
    // Only select the bundled homepage when we created it. Existing pages are never overwritten.
    if (isset($created['index'])) {
        update_option('show_on_front', 'page');
        update_option('page_on_front', $ids['index']);
    }
    update_option('sc_installed_version', '1.0.0');
    flush_rewrite_rules();
}
add_action('after_switch_theme', 'sc_setup_pages');
add_action('after_setup_theme', function () {
    add_theme_support('responsive-embeds');
    add_theme_support('editor-styles');
    add_editor_style('site/assets/site.css');
});

function sc_search_script() {
    $rows = array();
    foreach (get_option('sc_page_ids', array()) as $slug => $id) {
        if (get_post_status($id) !== 'publish') { continue; }
        $rows[] = array('t' => get_the_title($id), 'u' => get_permalink($id), 's' => '',
            'd' => wp_trim_words(wp_strip_all_tags(get_post_field('post_content', $id)), 25));
    }
    return '<script>window.PARISH_SEARCH=' . wp_json_encode($rows, JSON_HEX_TAG | JSON_HEX_AMP | JSON_HEX_APOS | JSON_HEX_QUOT) . ';</script>';
}
