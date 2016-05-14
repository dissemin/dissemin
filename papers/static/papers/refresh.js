function init_paper_module (config) {
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

  function flashMessages (messages) {
    var $messages = $('.messages > div')
    // Empty previous messages.
    $messages.remove()

    for (var index = 0 ; index < messages.length ; index += 1) {
      var message = messages[index]
      var classes = [
        'alert',
        'alert-warning'
      ].concat(messages.tags || [])

      var html = (
        '<div class="' + classes.join(' ') + '">' +
          '<p>' + message.text + '</p>' +
        '</div>')
      
      // Insert new message one by one.
      $(html).appendTo('.messages')
    }
  }

  function refreshPapers () {
    return fetch(config.refreshURL, {
      credentials: 'same-origin',
      headers: {
        "Content-Type": "application/json"
      }
    })
      .then(function (response) {
        return response.json()
      }).then(function (data) {
        config.paperSearchResultsNode.html(data.listPapers)
        updateStats(data.stats)
        flashMessages(data.messages)
        config.nbPapersFoundNode.text(data.stats.numtot)

        if (data.display) {
          // We update the status text if we have new status.
          config.harvestingStatusNode.text(data.display)
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
      return fetch(refetchURL, {
        credentials: 'same-origin'
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
      return fetch(setResearcherURL, {
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
}
