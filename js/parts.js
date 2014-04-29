/**
 * Various parts used in application.
 */
define(['underscore', 'backbone'], function(_, Backbone) {
  var parts = {};

  // Models
  parts.BaseModel = Backbone.Model.extend({

  });
  parts.RepoModel = Backbone.Model.extend({
    idAttribute: 'repo_id'
  });
  parts.UserModel = Backbone.Model.extend({
    idAttribute: 'user_id'
  });

  // Collections
  parts.BaseCollection = Backbone.Collection.extend({
    baseURL: 'https://premium.scraperwiki.com/dg5k2oq/f2c29454fb4f4cf/sql/?q=[[[QUERY]]]',

    initialize: function(models, options) {
      this.options = options;
    }
  });

  parts.RepoCollection = parts.BaseCollection.extend({
    model: parts.RepoModel,

    url: function() {
      var options = this.options.state.toJSON();
      query = "SELECT * FROM repos WHERE ";
      query += (options.include_forked) ? "is_fork >= 0 " : "is_fork = 0 ";
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

  return parts;
});
