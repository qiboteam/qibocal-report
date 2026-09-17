- the search filters section content is a bit larger than the sidebar size, and it
  triggers the horizontal scrollbar. fit it to the size
- paginate reports, both on frontend and backend
  - on the frontend, it should only receive the content for the current page, and only
    after start pre-fetching the pages that are accessible from the page navigation
  - on the backend, it should cache the indexing, and only invalidate if there is a more
    recent modification
