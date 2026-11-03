import { AlertCircle, Lock } from 'lucide-react'
import { useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'

import { canEditProduct, useAuth } from '../auth/useAuth'
import { ProductImage } from '../components/catalog/ProductImage'
import { Badge } from '../components/ui/Badge'
import { Button } from '../components/ui/Button'
import { EmptyState } from '../components/ui/EmptyState'
import { ErrorState } from '../components/ui/ErrorState'
import { FormField } from '../components/ui/FormField'
import { FormSection } from '../components/ui/FormSection'
import { Input } from '../components/ui/Input'
import { PageHeader } from '../components/ui/PageHeader'
import { Select } from '../components/ui/Select'
import { PageSpinner } from '../components/ui/Spinner'
import { Textarea } from '../components/ui/Textarea'
import { useToast } from '../components/ui/toastContext'
import { useBrands, useCategories } from '../hooks/useCatalogOptions'
import { useDebounce } from '../hooks/useDebounce'
import { useProductMutations } from '../hooks/useProductMutations'
import { useProduct } from '../hooks/useProducts'
import { parseTags, validateProduct } from '../lib/validation'

const EMPTY_FORM = {
  name: '',
  brand: '',
  category: '',
  price: '',
  description: '',
  tags: '',
  image_url: '',
  gtin: '',
  pack_size: '',
  variant: '',
}

/** API product → form values (everything as strings, tags comma-joined). */
function fromProduct(product) {
  return {
    name: product.name,
    brand: product.brand,
    category: String(product.category),
    price: product.price,
    description: product.description,
    tags: (product.tags || []).join(', '),
    image_url: product.image_url || '',
    gtin: product.gtin || '',
    pack_size: product.pack_size || '',
    variant: product.variant || '',
  }
}

/** Form values → API payload. Trims text and turns tags back into a list. */
function toPayload(values) {
  return {
    name: values.name.trim(),
    brand: values.brand.trim(),
    category: Number(values.category),
    price: values.price.trim(),
    description: values.description.trim(),
    tags: parseTags(values.tags),
    image_url: values.image_url.trim(),
    gtin: values.gtin.trim(),
    pack_size: values.pack_size.trim(),
    variant: values.variant.trim(),
  }
}

export function ProductFormPage() {
  const { id } = useParams()
  const isEdit = Boolean(id)
  const navigate = useNavigate()
  const { user } = useAuth()
  const toast = useToast()
  const existing = useProduct(id)
  const categories = useCategories()
  const brands = useBrands()
  const { create, update } = useProductMutations()

  const [values, setValues] = useState(EMPTY_FORM)
  const [errors, setErrors] = useState({})
  const [formError, setFormError] = useState(null)
  const [loadedId, setLoadedId] = useState(null)

  // Once the product we're editing arrives, fill the form with it (one time per product).
  if (existing.data && existing.data.id !== loadedId) {
    setLoadedId(existing.data.id)
    setValues(fromProduct(existing.data))
  }

  const set = (field) => (event) => {
    const value = event.target.value
    setValues((current) => ({ ...current, [field]: value }))
    if (errors[field]) setErrors((current) => ({ ...current, [field]: undefined }))
  }

  const mutation = isEdit ? update : create
  const tags = parseTags(values.tags)
  // Don't fetch a half-typed URL on every keystroke; preview once typing pauses.
  const previewUrl = useDebounce(values.image_url.trim(), 500)

  const submit = (event) => {
    event.preventDefault()
    const problems = validateProduct(values)
    setErrors(problems)
    setFormError(null)
    if (Object.keys(problems).length) {
      document.getElementById(`field-${Object.keys(problems)[0]}`)?.focus()
      return
    }

    const payload = toPayload(values)
    const request = isEdit ? { id, data: payload } : payload
    mutation.mutate(request, {
      onSuccess: (product) => {
        toast.success(isEdit ? 'Product updated.' : `Added “${product.name}” to the catalog.`)
        navigate(`/products/${product.id}`)
      },
      onError: (error) => {
        setErrors(error.fieldErrors())
        setFormError(error.formMessage())
        window.scrollTo({ top: 0, behavior: 'smooth' })
      },
    })
  }

  if (isEdit && existing.isPending) return <PageSpinner />
  if (isEdit && existing.isError) {
    return <ErrorState error={existing.error} onRetry={existing.refetch} title="Couldn't load this product" />
  }
  if (isEdit && !canEditProduct(user, existing.data)) {
    return (
      <EmptyState
        icon={Lock}
        title="You can't edit this product"
        description="Only the person who added it, or a staff member, can change it."
        action={<Button to={`/products/${id}`}>View product</Button>}
      />
    )
  }

  const categoryOptions = (categories.data || []).map((category) => ({
    value: String(category.id),
    label: category.full_path,
  }))

  return (
    <form onSubmit={submit} noValidate>
      <PageHeader
        breadcrumb={
          isEdit
            ? [{ label: 'Catalog', to: '/' }, { label: existing.data.name, to: `/products/${id}` }, { label: 'Edit' }]
            : [{ label: 'Catalog', to: '/' }, { label: 'New product' }]
        }
        title={isEdit ? 'Edit product' : 'New product'}
        subtitle="Fill in what a shelf camera needs to tell this SKU apart from its look-alikes."
      />

      {formError ? (
        <div className="mb-5 flex items-start gap-2.5 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700" role="alert">
          <AlertCircle className="mt-0.5 size-4 shrink-0" aria-hidden="true" />
          {formError}
        </div>
      ) : null}

      <div className="grid gap-6 lg:grid-cols-[1fr_340px]">
        <div className="space-y-6">
          <FormSection title="Basics" description="What the product is called and where it sits in the catalog.">
            <FormField label="Product name" htmlFor="field-name" error={errors.name}>
              <Input id="field-name" value={values.name} onChange={set('name')} invalid={Boolean(errors.name)} placeholder="e.g. Good Day Butter Cookies" maxLength={200} />
            </FormField>
            <div className="grid gap-4 sm:grid-cols-2">
              <FormField label="Brand" htmlFor="field-brand" error={errors.brand}>
                <Input id="field-brand" value={values.brand} onChange={set('brand')} invalid={Boolean(errors.brand)} placeholder="e.g. Britannia" list="brand-options" maxLength={100} />
                <datalist id="brand-options">
                  {(brands.data || []).map((brand) => (
                    <option key={brand} value={brand} />
                  ))}
                </datalist>
              </FormField>
              <FormField label="Price" htmlFor="field-price" error={errors.price} hint="Maximum retail price, in rupees.">
                <Input id="field-price" type="text" inputMode="decimal" value={values.price} onChange={set('price')} invalid={Boolean(errors.price)} placeholder="0.00" leading="₹" />
              </FormField>
            </div>
            <FormField label="Category" htmlFor="field-category" error={errors.category} hint="Pick the most specific category you can. Cameras need the full path.">
              <Select id="field-category" value={values.category} onChange={set('category')} invalid={Boolean(errors.category)} placeholder="Choose a category" options={categoryOptions} />
            </FormField>
          </FormSection>

          <FormSection title="Description" description="Factual packaging details. No invented claims.">
            <FormField label="Description" htmlFor="field-description" error={errors.description} hint={`${values.description.length}/2000`}>
              <Textarea id="field-description" rows={5} value={values.description} onChange={set('description')} invalid={Boolean(errors.description)} placeholder="Two or three sentences about the product and its pack." maxLength={2000} />
            </FormField>
            <FormField label="Tags" htmlFor="field-tags" error={errors.tags} optional hint="Comma separated, up to 10.">
              <Input id="field-tags" value={values.tags} onChange={set('tags')} invalid={Boolean(errors.tags)} placeholder="biscuits, butter, cookies" />
              {tags.length ? (
                <div className="flex flex-wrap gap-1.5 pt-1">
                  {tags.map((tag) => (
                    <Badge key={tag}>{tag}</Badge>
                  ))}
                </div>
              ) : null}
            </FormField>
          </FormSection>
        </div>

        <aside className="space-y-6">
          <FormSection title="Pack shot" description="A sharp, straight-on photo of the front of the pack.">
            <ProductImage key={previewUrl} src={previewUrl} alt="Pack shot preview" className="aspect-square w-full" iconClassName="size-8" />
            <FormField label="Image URL" htmlFor="field-image_url" error={errors.image_url} optional>
              <Input id="field-image_url" type="url" value={values.image_url} onChange={set('image_url')} invalid={Boolean(errors.image_url)} placeholder="https://…" />
            </FormField>
          </FormSection>

          <FormSection title="Identifiers" description="What tells this SKU apart from its look-alikes.">
            <FormField label="GTIN / barcode" htmlFor="field-gtin" error={errors.gtin} optional hint="8, 12, 13 or 14 digits. The check digit is verified.">
              <Input id="field-gtin" inputMode="numeric" value={values.gtin} onChange={set('gtin')} invalid={Boolean(errors.gtin)} placeholder="8901063010574" className="font-mono" />
            </FormField>
            <FormField label="Pack size" htmlFor="field-pack_size" error={errors.pack_size} optional>
              <Input id="field-pack_size" value={values.pack_size} onChange={set('pack_size')} invalid={Boolean(errors.pack_size)} placeholder="250 g" maxLength={50} />
            </FormField>
            <FormField label="Variant" htmlFor="field-variant" error={errors.variant} optional hint="Flavour, type or edition, e.g. Chocolate.">
              <Input id="field-variant" value={values.variant} onChange={set('variant')} invalid={Boolean(errors.variant)} placeholder="Butter" maxLength={100} />
            </FormField>
          </FormSection>
        </aside>
      </div>

      <div className="mt-6 flex items-center justify-end gap-2 border-t border-gray-200 pt-4">
        <Button to={isEdit ? `/products/${id}` : '/'}>Cancel</Button>
        <Button type="submit" variant="primary" loading={mutation.isPending}>
          {isEdit ? 'Save changes' : 'Add product'}
        </Button>
      </div>
    </form>
  )
}
