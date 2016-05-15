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
    return fetch(url, Object.assign(
      {},
      config,
      {
        headers: Object.assign({}, config.headers || {}, {
          'X-CSRFToken': csrftoken,
          'Content-Type': 'application/json'
        }),
        credentials: 'include'
      }
    ))
  }

  var MARK_AS_READ = gettext('Do not show this message anymore')

  function addWaitingArea (animatedBirdGIF, container, currentTask) {
    container.html(
      "<div id='waitingArea'>" +
        "<span class='waitingBird'>" +
          "<img src='" + animatedBirdGIF + "' alt='Paper animated bird' />" +
        "</span>" +
        "<br />" +
        "<span id='harvestingStatus'>" +
          currentTask +
        "</span>" +
        "<span>…</span>" +
        "<br />" +
      "</div>"
    )

    config.waitingAreaNode = $('#waitingArea')
  }

  function notifyWaitingArea (message) {
    addWaitingArea(config.animatedBirdGIF,
                   config.waitingAreaContainerNode,
                   message)
  }

  function renderReason (reason) {
    if (reason === 'NO_AUTHOR') {
      return gettext('No author')
    } else if (reason === 'NO_TITLE') {
      return gettext('No title')
    } else if (reason === 'INVALID_PUB_DATE') {
      return gettext('Invalid publication date')
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
              '"%(name)s" is ignored with the following reason: %(reason)s'
            ),
            {
              name: paper.title,
              reason: renderReason(paper.skip_reason)
            },
            true) + '</p>'
          } else {
            return '<p>' + gettext('A paper has been ignored, because it has no name') + '</p>'
          }
        }).map(function (paper) {
          return '<li>' + paper + '</li>'
        })

        var detailed_informations = '<ul class="more-information">' + detailed_papers.join('\n') + '</ul>'

        html += '<p>' + human_message + '</p>'
        html += detailed_informations
        html += '<div class="message-actions">'
          html += '<button data-id=' + message.id + ' class="btn btn-mark-as-read">' + MARK_AS_READ + '</button>'
          html += '<button class="btn btn-show-more-informations">' + gettext('Show more informations') + '</button>'
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
        $button.text(gettext('Show less informations'))
      } else {
        $more_information.removeClass('shown')
        $button.text(gettext('Show more informations'))
      }
    })
  }

  function refreshPapers () {
    return call_api(config.refreshURL)
      .then(function (response) {
        return response.json()
      }).then(function (data) {
        config.paperSearchResultsNode.html(data.listPapers)
        updateStats(data.stats)
        flashMessages(parseMessages(data.messages))
        config.nbPapersFoundNode.text(data.stats.numtot)

        if (data.display) {
          // We update the status text if we have new status.
          config.harvestingStatusNode().text(data.display)
          setTimeout(refreshPapers, 3000)
        } else {
          config.waitingAreaNode.fadeOut(function () {
            config.waitingAreaNode.hide()
          })
        }

        console.log('Paper refresh has succeed', data)
      })
      .catch(function (error) {
        console.error('Paper refresh has failed', error)
        config.waitingAreaNode.fadeOut(function () {
          config.waitingAreaNode.hide()
        })
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
          setTimeout(refreshPapers, 1000)
        })
        .catch(function (error) {
          console.error('Refetch process has failed', error)
        })
    }
  }

  function updateResearcherDepartment (setResearcherURL) {
    return function (event) {
      return call_api(setResearcherURL, {
        method: 'POST',
        body: new BodyForm(config.affiliationForm),
        headers: {
          "Content-Type": "application/json"
        }
      })
      .then(function (response) {
        console.log('Department was updated', response)
      })
      .catch(function (error) {
        console.error('Department was not updated', error)
      })
    }
  }

  // Set up the popover for the logo help.
  config.logoHelpNode.popover({
    trigger: 'hover'
  })


  // When we click on the refetch button, we reload the publications.
  config.refetchButtonNode.click(
    refetchPublications(config.refetchURL, config.refreshMessage)
  )

  // If we have a current task running, we add message status on the waiting area.
  // And we schedule a refresh paper to poll new results from the server.
  if (config.currentTask) {
    notifyWaitingArea(config.currentTask)
    setTimeout(refreshPapers, 1500)
  }

  if (config.isSuperUser) {
    config.affiliationForm.change(
      updateResearcherDepartment(config.setResearcherDepartmentURL)
    )
  }

  if (config.initialMessages) {
    var messages = parseMessages(config.initialMessages)
    flashMessages(messages)
  }
}
