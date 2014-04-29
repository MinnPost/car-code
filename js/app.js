/**
 * Main application file.
 */

// Create main application
define(['jquery', 'underscore', 'ractive', 'ractive-backbone', 'ractive-transitions-fade', 'mpConfig', 'parts'], function($, _, Ractive, RB, RTF, mpConfig, p) {

  // Constructor for app
  var App = function(options) {
    this.el = '#application-container';
    this.$el = $(this.el);
    this.templateApplication = $('#application-template').html();
    this.start();
  };

  // Extend with custom methods
  _.extend(App.prototype, {

    // Initializer
    start: function() {
      // Model to help with state and options
      this.state = new p.BaseModel({
        sort: 'created',
        include_forked: false,
        language: null,
        search: null
      });

      // Collections
      this.users = new p.UserCollection(null, { state: this.state });
      this.repos = new p.RepoCollection(null, { state: this.state });

      // Main view for application
      this.applicationView = new Ractive({
        el: this.$el,
        template: this.templateApplication,
        data: {
          users: this.users,
          repos: this.repos,
          state: this.state
        },
        adapt: ['Backbone']
      });

      // Get data
      this.users.fetch();
      this.repos.fetch();
    }
  });

  return App;
});
