/**
 * Configures require.
 */
require.config({
  shim: {
  },
  baseUrl: 'js',
  paths: {
    'requirejs': '../bower_components/requirejs/require',
    'almond': '../bower_components/almond/almond',
    'text': '../bower_components/text/text',
    'jquery': '../bower_components/jquery/dist/jquery',
    'underscore': '../bower_components/underscore/underscore',
    'backbone': '../bower_components/backbone/backbone',
    'moment': '../bower_components/moment/moment',
    'ractive': '../bower_components/ractive/ractive',
    'ractive-backbone': '../bower_components/ractive-backbone/ractive-adaptors-backbone',
    'ractive-events-tap': '../bower_components/ractive-events-tap/ractive-events-tap',
    'ractive-transitions-fade': '../bower_components/ractive-transitions-fade/ractive-transitions-fade',
    'mpConfig': '../bower_components/minnpost-styles/dist/minnpost-styles.config',
    'mpFormatters': '../bower_components/minnpost-styles/dist/minnpost-styles.formatters',
    'mpNav': '../bower_components/minnpost-styles/dist/minnpost-styles.nav'
  }
});

/**
 * Run application
 */
require(['jquery', 'app'], function($, App) {
  $(document).ready(function() {
    var app = new App();
  });
});
