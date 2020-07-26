import React, { Component } from 'react';
import ReactPlayer from "react-player/lazy"
import algoliasearch from 'algoliasearch/lite';
import {
  InstantSearch,
  Hits,
  SearchBox,
  Pagination,
  Highlight,
} from 'react-instantsearch-dom';
import PropTypes, { array } from 'prop-types';
import './App.css';

const searchClient = algoliasearch(
  'DDZ5A54Y8V',
  'd920e42fae52d117a177ecb4b02417e7'
);

class App extends Component {
  render() {
    return (
      <div>
        <header className="header">
          <h1 className="header-title">
            <a href="/">video-search-enhancer-app</a>
          </h1>
          <p className="header-subtitle">
            using{' '}
            <a href="https://github.com/algolia/react-instantsearch">
              React InstantSearch
            </a>
          </p>
        </header>

        <div className="container">
          <InstantSearch searchClient={searchClient} indexName="videos">
            <div className="search-panel">
              <div className="search-panel__results">
                <SearchBox
                  className="searchbox"
                  translations={{
                    placeholder: '',
                  }}
                />
                <Hits hitComponent={Hit} />

                <div className="pagination">
                  <Pagination />
                </div>
              </div>
            </div>
          </InstantSearch>
        </div>
      </div>
    );
  }
}

function Hit(props) {
  console.log("hit: ", props)
  
  console.log("transcript: ", props.hit._highlightResult.transcript);
  // var highlightedRe = /[a-z]+<\/ais-highlight-0000000000>[a-z]*/gi;
  var highlightedRe = /((<ais-highlight-0000000000>[\w]+<\/ais-highlight-0000000000>(\s|[a-z]+))+)/gi;

  // var matches = highlightedRe.match(props.hit._highlightResult.transcript.value);

  var matches = props.hit._highlightResult.transcript.value.match(highlightedRe) || []
  console.log("matches: ", matches)

  matches.sort(function(a, b) {
    // ASC  -> a.length - b.length
    // DESC -> b.length - a.length
    return b.length - a.length;
  });

  console.log("after sort, longest matches: ", matches[0])
  var startingTimestamp = 0

  if (matches.length >= 1) {
    var longestMatchWords = matches[0].replace(/<ais-highlight-0000000000>/gi, "").replace(/<\/ais-highlight-0000000000>/gi, "").trim().split(" ")
    console.log("longestMatchWords: ", longestMatchWords)

    if (longestMatchWords.length == 1) {
      // for single match word
      var longestMatchWord = longestMatchWords[0];
      console.log("longest word indicies: ", props.hit.word_timestamps[longestMatchWord])

      if (props.hit.word_timestamps[longestMatchWord.toLowerCase()]) {
        startingTimestamp = props.hit.word_timestamps[longestMatchWord.toLowerCase()][0]
      }
      console.log("longest word starting index: ", startingTimestamp)
    } else if (longestMatchWords.length == 2) {
      // for two match words
      var firstWord = longestMatchWords[0].toLowerCase()
      var lastWord = longestMatchWords[longestMatchWords.length-1].toLowerCase()
      
      var firstWordIndices = props.hit.word_timestamps[firstWord] || []
      var lastWordIndices = props.hit.word_timestamps[lastWord] || []

      var i = 0
      var j = 0
      var diff = Number.POSITIVE_INFINITY
      var startIdx = 0

      while (i < firstWordIndices.length && j < lastWordIndices.length) {
        if (firstWordIndices[i] > lastWordIndices[j]) {
          j++
          continue
        }
      
        if (lastWordIndices[j] - firstWordIndices[i] < diff) {
          diff = lastWordIndices[j] - firstWordIndices[i]
          startIdx = i
        }
      
        if (firstWordIndices[i] <= lastWordIndices[j]) {
          i++
        } else {
          j++
        }
      }

      startingTimestamp = firstWordIndices[startIdx]

    } else if (longestMatchWords.length > 2) {
      // for more than two match words
      console.log("longestMatchWords ", longestMatchWords)
      var firstWord = longestMatchWords[0].toLowerCase()
      var lastWord =  longestMatchWords[longestMatchWords.length-1].toLowerCase()
      var middleWord = longestMatchWords[Math.floor(longestMatchWords.length/2)].toLowerCase()

      var firstWordIndices = props.hit.word_timestamps[firstWord]
      var middleWordIndices = props.hit.word_timestamps[middleWord]
      var lastWordIndices = props.hit.word_timestamps[lastWord]

      var i = 0
      var j = 0
      var k = 0
      var diff = Number.POSITIVE_INFINITY
      var startIdx = 0

      while (i < firstWordIndices.length && j < middleWordIndices.length && k < lastWordIndices.length) {
        if (firstWordIndices[i] > middleWordIndices[j]) {
          j++
          continue
        }

        if (middleWordIndices[j] > lastWordIndices[k]) {
          k++
          continue
        }

        if ((middleWordIndices[j] - firstWordIndices[i]) + (lastWordIndices[k] - middleWordIndices[j]) < diff) {
          diff = (middleWordIndices[j] - firstWordIndices[i]) + (lastWordIndices[k] - middleWordIndices[j])
          startIdx = i
        }

        if (firstWordIndices[i] <= middleWordIndices[j] && firstWordIndices[i] <= lastWordIndices[k]) {
          i++
        } else if (middleWordIndices[j] <= lastWordIndices[k]) {
          j++
        } else {
          k++
        }
      }

      startingTimestamp = firstWordIndices[startIdx]
    }
  }

  console.log("startingTimestamp: ", startingTimestamp)

  return (
    <article>
      <ReactPlayer
        url={props.hit.video_url + "&t=" + startingTimestamp}
        controls={true}
        width="365px"
        height="265px"
      />
      <Highlight attribute="transcript" hit={props.hit} />
    </article>
  );
}

Hit.propTypes = {
  hit: PropTypes.object.isRequired,
};

export default App;