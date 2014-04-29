/**
 * Various parts used in application.
 */
define(['underscore', 'backbone', 'moment', 'mpConfig'], function(_, Backbone, moment, mpConfig) {
  var parts = {};
  var color = 0;
  var colors = _.toArray(mpConfig['colors-data']).reverse();

  // Models
  parts.StateModel = Backbone.Model.extend({
  });
  parts.RepoModel = Backbone.Model.extend({
    idAttribute: 'repo_id'
  });
  parts.UserModel = Backbone.Model.extend({
    idAttribute: 'user_id'
  });

  parts.LanguageModel = Backbone.Model.extend({
    idAttribute: 'language',

    initialize: function(attributes, options) {
      if (!this.get('color')) {
        this.set('color', colors[color]);
        color = (color === colors.length - 1) ? 0 : color + 1;
      }
    },
  });

  // Collections
  parts.BaseCollection = Backbone.Collection.extend({
    baseURL: 'https://premium.scraperwiki.com/dg5k2oq/f2c29454fb4f4cf/sql/?q=[[[QUERY]]]',

    initialize: function(models, options) {
      this.options = options;
    },

    parse: function(response) {
      return _.map(response, function(r, ri) {
        if (r.created) {
          r.created = moment(r.created);
        }
        if (r.updated) {
          r.updated = moment(r.updated);
        }
        if (!_.isUndefined(r.language)) {
          r.language = (r.language) ? r.language : 'unknown';
        }
        return r;
      });
    }
  });

  parts.RepoCollection = parts.BaseCollection.extend({
    model: parts.RepoModel,

    url: function() {
      var options = this.options.state.toJSON();

      query = "SELECT * FROM repos WHERE ";
      query += (options.include_forked) ? "is_fork >= 0 " : "is_fork = 0 ";
      query += (options.language && options.language !== 'unknown') ?
        "AND language = '" + options.language + "' " : " ";
      query += (options.language && options.language === 'unknown') ?
        "AND (language = '' OR language IS NULL) " : " ";
      query += (!options.search) ? " " :
        "AND repo_id IN (SELECT repo_id FROM repo_index WHERE content MATCH '" + options.search + "')";
      query += "ORDER BY " + ((options.sort) ? options.sort + " " : "created ");
      query += (options.direction) ? options.direction + " " : "DESC ";
      query += (options.limit) ? "LIMIT " + options.limit + " " : "LIMIT 100 ";

      return this.baseURL.replace('[[[QUERY]]]', encodeURIComponent(query));
    }
  });

  parts.UserCollection = parts.BaseCollection.extend({
    model: parts.UserModel,

    url: function() {
      query = "SELECT * FROM users ORDER BY name";
      return this.baseURL.replace('[[[QUERY]]]', encodeURIComponent(query));
    }
  });

  parts.LanguageCollection = parts.BaseCollection.extend({
    model: parts.LanguageModel,

    url: function() {
      query = "SELECT language, COUNT(*) AS count FROM repos GROUP BY language ORDER BY language";
      return this.baseURL.replace('[[[QUERY]]]', encodeURIComponent(query));
    }
  });

  return parts;
});
