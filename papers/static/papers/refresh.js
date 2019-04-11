function init_paper_module (config) {
    // using jQuery
  function getCookie(name) {
      var cookieValue = null;
      if (document.cookie && document.cookie != '') {
          var cookies = document.cookie.split(';');
          for (var i = 0; i < cookies.length; i++) {
              var cookie = jQuery.trim(cookies[i]);
              // Does this cookie string begin with the name we want?
              if (cookie.substring(0, name.length + 1) == (name + '=')) {
                  cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                  break;
              }
          }
      }
      return cookieValue;
  }

  function call_api(url, user_config) {
    var csrftoken = getCookie('csrftoken');
    var config = user_config || {}
    return fetch(url, $.extend(
      {},
      config,
      {
        headers: $.extend({}, config.headers || {}, {
          'X-CSRFToken': csrftoken,
          'Content-Type': 'application/json'
        }),
        credentials: 'include'
      }
    ))
  }

  // Taken from https://gist.github.com/kares/956897#gistcomment-802666
  function parseParams (query) {
    var re = /([^&=]+)=?([^&]*)/g;
    var decode = function(str) {
      return decodeURIComponent(str.replace(/\+/g, ' '));
    };
    var params = {}, e;
    if (query) {
      if (query.substr(0, 1) == '?') {
        query = query.substr(1);
      }

      while (e = re.exec(query)) {
        var k = decode(e[1]);
        var v = decode(e[2]);
        if (params[k] !== undefined) {
          if (!$.isArray(params[k])) {
            params[k] = [params[k]];
          }
          params[k].push(v);
        } else {
          params[k] = v;
        }
      }
    }
    return params;
  };

  var MARK_AS_READ = gettext('Do not show this message anymore')

  function addWaitingArea () {
    $(
      "<div id='waitingArea'>" +
        "<span class='waitingBird'>" +
          "<img src='" + config.animatedBirdGIF + "' alt='Paper animated bird' />" +
        "</span>" +
        "<br />" +
        "<span id='harvestingStatus'></span>" +
        "<span>…</span>" +
        "<br />" +
      "</div>"
    ).hide().appendTo(config.waitingAreaContainerNode)

    config.waitingAreaNode = $('#waitingArea')
    config.harvestingStatusNode = $('#harvestingStatus')
  }
  addWaitingArea()

  function fadeOutWaitingArea () {
    config.waitingAreaNode.fadeOut()
  }

  function notifyWaitingArea (message) {
    config.harvestingStatusNode.html(message)
    config.waitingAreaNode.show()
  }

  function renderReason (reason) {
    if (reason === 'NO_AUTHOR') {
      return gettext('No author')
    } else if (reason === 'NO_TITLE') {
      return gettext('No title')
    } else if (reason === 'INVALID_PUB_DATE') {
      return gettext('Invalid publication date')
    } else if (reason === 'NO_PUBDATE') {
      return gettext('No publication date')
    } else {
      return gettext('Paper is invalid')
    }
  }

  function markMessageAsRead (messageId) {
    return call_api(Urls['inbox-read'](messageId), {
      method: 'POST'
    })
  }

  function parseMessages (messages) {
    return messages.map(function (message) {
      return JSON.parse(message)
    })
  }

  function flashMessages (messages) {
    var $messages = $('.messages > div')
    // Empty previous messages.
    $messages.remove()

    for (var index = 0 ; index < messages.length ; index += 1) {
      var message = messages[index]
      var classes = [
        'alert',
        'alert-warning',
        message.tag || ''
      ]

      var html = (
        '<div class="' + classes.join(' ') + '">'
      )

      if (message.payload.code === 'IGNORED_PAPERS') {
        var human_message = interpolate(ngettext(
          'We ignored %(count)s paper from your ORCiD profile.',
          'We ignored %(count)s papers from your ORCiD profile.',
          message.payload.papers.length
        ),
        { count: message.payload.papers.length },
        true)

        var detailed_papers = message.payload.papers.map(function (paper) {
          if (paper.title) {
            return '<p>' + interpolate(gettext(
              '"%(name)s" was ignored for the following reason: %(reason)s'
            ),
            {
              name: paper.title,
              reason: renderReason(paper.skip_reason)
            },
            true) + '</p>'
          } else {
            return '<p>' + gettext('A paper was ignored, because it has no name') + '</p>'
          }
        }).map(function (paper) {
          return '<li>' + paper + '</li>'
        })

        var detailed_informations = '<ul class="more-information">' + detailed_papers.join('\n') + '</ul>'

        html += '<p>' + human_message + '</p>'
        html += detailed_informations
        html += '<div class="message-actions">'
          html += '<button data-id=' + message.id + ' class="btn btn-mark-as-read">' + MARK_AS_READ + '</button>'
          html += '<button class="btn btn-show-more-informations">' + gettext('Show more information') + '</button>'
        html += '</div>'
      }

      html += '</div>'

      // Insert new message one by one.
      $(html).appendTo('.messages')
    }

    $('.btn-mark-as-read').click(function (evt) {
      var $button = $(evt.target)
      var $message = $button.parent().parent()

      var messageId = $(evt.target).attr('data-id')
      markMessageAsRead(messageId)
      $message.remove()
    })
    $('.btn-show-more-informations').click(function (evt) {
      var $button = $(evt.target)
      var $message = $button.parent().parent()
      var $more_information = $message.find('.more-information')

      if (!$more_information.hasClass('shown')) {
        $more_information.addClass('shown')
        $button.text(gettext('Show less information'))
      } else {
        $more_information.removeClass('shown')
        $button.text(gettext('Show more information'))
      }
    })
  }

  function updateData (data) {
    config.paperSearchResultsNode.html(data.listPapers)
    updateStats(data.stats)
    config.nbPapersFoundNode.text(
      interpolate(
        ngettext(
          '%s paper found',
          '%s papers found',
          data.nb_results
        ),
        [formatNumbersThousands(data.nb_results)]
      )
    )
    flashMessages(parseMessages(data.messages))
    config.hook()

    var parsedQuery = parseParams(query);
    fillForm('#searchPapers', parsedQuery)
    fillForm('#searchPapersStatistics', parsedQuery)
    $('a[data-sort-by]').each(function() {
      var sortByQuery = jQuery.extend({}, parsedQuery);
      sortByQuery['sort_by'] = $(this).attr('data-sort-by');
      // Update dropdown links hrefs
      $(this).attr('href', $.param(sortByQuery, true));
      // Update button label
      if ($(this).attr('data-sort-by') === parsedQuery['sort_by']) {
        $('#sortByDropdown .btn-label').text($(this).text());
      }
    });
  }

  var refreshTask
  var query = window.location.search

  // A user-requested refresh dims the paper list.
  function refreshPapers () {
    config.paperSearchResultsNode.children().css('opacity', '0.5')
    window.clearTimeout(refreshTask)
    _refreshPapers(800)
  }

  function _refreshPapers (delay) {
    refreshTask = window.setTimeout(_refresh, delay)
  }

  function _refresh () {
    var this_query = query
    return call_api(config.refreshURL + this_query)
      .then(function (response) {
        return response.json()
      }).then(function (data) {
        updateData(data)

        if (data.display) {
          // We update the status text if we have new status.
          notifyWaitingArea(data.display)
          _refreshPapers(3000)
        } else {
          fadeOutWaitingArea()
        }

        // Handle empty query string case nicely
        // See https://stackoverflow.com/questions/46805986/replacestate-with-empty-string-javascript
        if (window.location.search === this_query) {
          window.history.replaceState(data, "", document.location.search || window.location.pathname)
        } else {
          window.history.pushState(data, "", this_query || window.location.pathname)
        }

      })
      .catch(function (error) {
        console.error('Paper refresh has failed', error)
        fadeOutWaitingArea()
      })
  }

  function refetchPublications (refetchURL, refreshMessage) {
    return function (evt) {
      console.log('Dissemin is refetching your publications...', refetchURL)
      return call_api(refetchURL, {
        credentials: 'include'
      })
        .then(function (response) {
          console.log('Refetch process is a success.', response)
          notifyWaitingArea(refreshMessage)
          refreshPapers()
        })
        .catch(function (error) {
          console.error('Refetch process has failed', error)
        })
    }
  }

  // Set up the popover for the logo help.
  config.logoHelpNode.popover({
    trigger: 'hover'
  })

  // When we click on the refetch button, we reload the publications.
  config.refetchButtonNode.click(
    refetchPublications(config.refetchURL, config.refetchMessage)
  )

  // If we have a current task running,
  // we schedule a paper refresh to poll new results from the server.
  if (config.currentTask) {
    notifyWaitingArea(config.currentTask)
    _refreshPapers(1500)
  }

  if (config.initialMessages) {
    var messages = parseMessages(config.initialMessages)
    flashMessages(messages)
  }

  function refreshWithQuery(_query) {
    query = _query ? '?' + _query : '';
    refreshPapers()
  }

  function fillForm(form, parsedQuery) {
    var test = function (name, shouldBe) {
      var value = parsedQuery[name];
      if (value instanceof Array) {
        return value.indexOf(shouldBe) !== -1;
      }
      return value === shouldBe
    }
    $(form + ' :input, :input[form="' + form + '"]').each(function () {
      switch (this.type) {
        case 'checkbox':
          this.checked = test(this.name, this.value);
          break
        case 'search':
        case 'text':
          $(this).val(parsedQuery[this.name] || '')
          break
      }
    })

    // Update hidden fields
    $(form + ' :input.getStorage[type="hidden"]').val('');
    Object.keys(parsedQuery).forEach(function (key) {
      var value = parsedQuery[key];
      var hiddenFields = $(form + ' :input.getStorage[type="hidden"][name="' + key + '"]');
      if (hiddenFields.length > 1) {
        if (! (value instanceof Array)) {
          value = [value];
        }
        hiddenFields.each(function(idx) {
          $(this).val(value[idx] || '');
        });
      }
      else {
        hiddenFields.val(value);
      }
    });
  }

  window.onpopstate = function (e) {
    query = document.location.search
    if (e.state) {
      updateData(e.state)
    } else {
      refreshPapers()
    }
  }

  $('#searchPapers, #searchPapersStatistics').submit(function (e) {
    e.preventDefault()
    var $inputs = $(':input', this)
    // Remove empty parameters from queries for cleaner URLs.
    var disableEmptyInputs = function (b) {
      $inputs.each(function (){
        if (!$(this).val())
          this.disabled = b
      })
    }
    disableEmptyInputs(true)
    notifyWaitingArea(config.refreshMessage)
    refreshWithQuery($.param($(this).serializeArray()))
    disableEmptyInputs(false)
  });

  $('.sort-by-dropdown a').on('click', function (e) {
    e.preventDefault();
    notifyWaitingArea(config.refreshMessage)
    var href = $(this).attr('href');
    if (href[0] == '?') {
      // Remove leading '?' character
      href = href.slice(1);
    }
    if (href[0] == '&') {
      // Remove a leading '&' character afterwards
      href = href.slice(1);
    }
    refreshWithQuery(href);
  });
}
