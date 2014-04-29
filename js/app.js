/**
 * Main application file.
 */

// Create main application
define(['jquery', 'underscore', 'ractive', 'ractive-backbone', 'ractive-transitions-fade', 'ractive-events-tap', 'parts'], function($, _, Ractive, RB, RTF, RET, p) {

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
      var thisApp = this;

      // Model to help with state and options
      this.state = new p.StateModel({
        sort: 'created',
        include_forked: false,
        language: '',
        search: '',
        limit: 50
      });

      // Collections
      this.users = new p.UserCollection(null, { state: this.state });
      this.repos = new p.RepoCollection(null, { state: this.state });
      this.languages = new p.LanguageCollection(null, { state: this.state });


      // Main view for application
      this.view = new Ractive({
        el: this.$el,
        template: this.templateApplication,
        data: {
          users: this.users,
          repos: this.repos,
          state: this.state,
          languages: this.languages,
          thing: true,
          getLanguage: function(id) {
            return thisApp.languages.get(id).toJSON();
          }
        },
        adapt: ['Backbone']
      });
      this.events();

      // Get data, get languages first
      this.languages.fetch().done(function() {
        thisApp.users.fetch();
        thisApp.repos.fetch();
      });
    },

    // Handle events
    events: function() {
      var thisApp = this;

      // If state model changes, update data
      this.state.on('change', function() {
        thisApp.update();
      });

      // General prevent
      this.view.on('prevent', function(e, sort) {
        e.original.preventDefault();
      });

      // Re sort
      this.view.on('sort', function(e, sort) {
        e.original.preventDefault();
        thisApp.state.set('sort', sort);
      });

      // Search.  We make people use the button to reduce number of calls
      this.view.on('search', function(e) {
        e.original.preventDefault();
        thisApp.state.set('search', this.get('search_proxy'));
      });
    },

    // Update data
    update: function() {
      //this.users.fetch();
      this.repos.reset();
      this.repos.fetch();
    }
  });

  return App;
});
