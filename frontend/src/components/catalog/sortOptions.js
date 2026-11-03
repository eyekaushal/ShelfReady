/** Matches the backend's `ordering` values (price, name, created_at, with "-" for descending). */
export const SORT_OPTIONS = [
  { value: '-created_at', label: 'Newest first' },
  { value: 'created_at', label: 'Oldest first' },
  { value: 'price', label: 'Price: low to high' },
  { value: '-price', label: 'Price: high to low' },
  { value: 'name', label: 'Name: A to Z' },
  { value: '-name', label: 'Name: Z to A' },
]
