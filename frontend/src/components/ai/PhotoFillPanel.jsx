import { AlertCircle, ImageUp, Info, Link2, Sparkles, X } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'

import { aiApi } from '../../api/aiApi'
import { toApiError } from '../../lib/apiError'
import { isCloudinaryEnabled, uploadToCloudinary } from '../../lib/cloudinary'
import { cn } from '../../lib/cn'
import { isHttpUrl } from '../../lib/validation'
import { Button } from '../ui/Button'
import { Input } from '../ui/Input'

const ACCEPTED = ['image/jpeg', 'image/png', 'image/webp']
const MAX_BYTES = 5 * 1024 * 1024

const MODES = [
  { value: 'upload', icon: ImageUp, label: 'Upload photo' },
  { value: 'url', icon: Link2, label: 'Image URL' },
]

/**
 * "Fill from photo": the user gives a pack shot (upload or URL), Claude reads it, and
 * `onFilled(result, imageUrl)` hands the suggested fields to the form. Nothing is saved here.
 *
 * Upload flow: with Cloudinary configured, the photo is uploaded first and its permanent URL
 * becomes the product's image; without it, the file is sent once for reading only.
 */
export function PhotoFillPanel({ enabled, onFilled }) {
  const [mode, setMode] = useState('upload')
  const [file, setFile] = useState(null)
  const [preview, setPreview] = useState(null)
  const [url, setUrl] = useState('')
  const [step, setStep] = useState(null) // null | 'uploading' | 'reading'
  const [error, setError] = useState(null)
  const [result, setResult] = useState(null) // {count, notes, stored}
  const [dragging, setDragging] = useState(false)
  const inputRef = useRef(null)
  const previewRef = useRef(null)

  // A local preview is an object URL; free it when replaced and when the panel unmounts.
  const showFile = (picked) => {
    if (previewRef.current) URL.revokeObjectURL(previewRef.current)
    previewRef.current = picked ? URL.createObjectURL(picked) : null
    setPreview(previewRef.current)
    setFile(picked)
  }
  useEffect(() => () => previewRef.current && URL.revokeObjectURL(previewRef.current), [])

  const chooseFile = (picked) => {
    setError(null)
    setResult(null)
    if (!picked) return
    if (!ACCEPTED.includes(picked.type)) return setError('Use a JPEG, PNG or WebP image.')
    if (picked.size > MAX_BYTES) return setError('Image must be 5 MB or smaller.')
    showFile(picked)
  }

  const clearFile = () => {
    showFile(null)
    if (inputRef.current) inputRef.current.value = ''
  }

  const canRead = enabled && !step && (mode === 'upload' ? Boolean(file) : isHttpUrl(url.trim()))

  const read = async () => {
    setError(null)
    setResult(null)
    try {
      let imageUrl = null
      let answer
      if (mode === 'url') {
        imageUrl = url.trim()
        setStep('reading')
        answer = await aiApi.extractFromUrl(imageUrl)
      } else if (isCloudinaryEnabled) {
        setStep('uploading')
        imageUrl = await uploadToCloudinary(file)
        setStep('reading')
        answer = await aiApi.extractFromUrl(imageUrl)
      } else {
        setStep('reading')
        answer = await aiApi.extractFromFile(file)
      }
      const count = onFilled(answer, imageUrl)
      setResult({ count, notes: answer.notes, stored: Boolean(imageUrl) })
    } catch (caught) {
      const apiError = toApiError(caught)
      const field = apiError.fieldErrors()
      setError(field.image_url || field.image || apiError.message)
    } finally {
      setStep(null)
    }
  }

  return (
    <section className="rounded-lg border border-gray-200 bg-white">
      <header className="flex items-start gap-3 border-b border-gray-100 px-5 py-3.5">
        <span className="flex size-8 shrink-0 items-center justify-center rounded-md bg-accent-soft text-accent">
          <Sparkles className="size-4" aria-hidden="true" />
        </span>
        <div className="min-w-0 flex-1">
          <h2 className="text-sm font-semibold text-gray-900">Fill from photo</h2>
          <p className="mt-0.5 text-xs text-gray-500">
            Claude reads the pack shot and suggests the fields below. You review everything before saving.
          </p>
        </div>
        {!enabled ? (
          <span className="inline-flex h-6 items-center rounded-md bg-gray-100 px-2 text-xs font-medium text-gray-600">
            AI unavailable
          </span>
        ) : null}
      </header>

      <div className="space-y-4 px-5 py-4">
        <div className="inline-flex h-9 items-center rounded-md border border-gray-200 bg-gray-50 p-0.5" role="group">
          {MODES.map((option) => (
            <button
              key={option.value}
              type="button"
              onClick={() => {
                setMode(option.value)
                setError(null)
              }}
              aria-pressed={mode === option.value}
              className={cn(
                'flex h-full items-center gap-1.5 rounded px-3 text-[13px] font-medium transition-colors',
                mode === option.value
                  ? 'bg-white text-gray-900 shadow-[0_1px_2px_rgb(0_0_0/0.08),0_0_0_1px_rgb(0_0_0/0.04)]'
                  : 'text-gray-500 hover:text-gray-900',
              )}
            >
              <option.icon className="size-4" aria-hidden="true" />
              {option.label}
            </button>
          ))}
        </div>

        {mode === 'upload' ? (
          file ? (
            <div className="flex items-center gap-3 rounded-md border border-gray-200 p-2">
              <img src={preview || ''} alt="" className="size-14 shrink-0 rounded border border-gray-200/80 bg-gray-50 object-contain" />
              <div className="min-w-0 flex-1">
                <p className="truncate text-[13px] font-medium text-gray-900">{file.name}</p>
                <p className="text-xs text-gray-500">
                  {(file.size / 1024 / 1024).toFixed(1)} MB ·{' '}
                  {isCloudinaryEnabled ? 'will be saved as the product image' : 'used once to read the pack'}
                </p>
              </div>
              <Button variant="ghost" size="icon" onClick={clearFile} aria-label="Remove photo" disabled={Boolean(step)}>
                <X className="size-4" />
              </Button>
            </div>
          ) : (
            <label
              onDragOver={(event) => {
                event.preventDefault()
                setDragging(true)
              }}
              onDragLeave={() => setDragging(false)}
              onDrop={(event) => {
                event.preventDefault()
                setDragging(false)
                chooseFile(event.dataTransfer.files?.[0])
              }}
              className={cn(
                'flex cursor-pointer flex-col items-center justify-center rounded-md border border-dashed px-4 py-6 text-center transition-colors',
                dragging ? 'border-accent bg-accent-soft' : 'border-gray-300 hover:border-gray-400 hover:bg-gray-50',
                !enabled && 'pointer-events-none opacity-60',
              )}
            >
              <ImageUp className="mb-2 size-5 text-gray-400" aria-hidden="true" />
              <span className="text-[13px] font-medium text-gray-700">Drop a pack shot here, or click to choose</span>
              <span className="mt-0.5 text-xs text-gray-500">JPEG, PNG or WebP, up to 5 MB</span>
              <input
                ref={inputRef}
                type="file"
                accept={ACCEPTED.join(',')}
                className="sr-only"
                onChange={(event) => chooseFile(event.target.files?.[0])}
                disabled={!enabled}
              />
            </label>
          )
        ) : (
          <Input
            type="url"
            value={url}
            onChange={(event) => {
              setUrl(event.target.value)
              setError(null)
            }}
            placeholder="https://… link to a front-of-pack photo"
            leading={<Link2 className="size-4" />}
            disabled={!enabled}
            aria-label="Pack shot image URL"
          />
        )}

        {error ? (
          <div className="flex items-start gap-2 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700" role="alert">
            <AlertCircle className="mt-0.5 size-4 shrink-0" aria-hidden="true" />
            {error}
          </div>
        ) : null}

        {result ? (
          <div className="flex items-start gap-2 rounded-md border border-accent-ring bg-accent-soft px-3 py-2 text-[13px] text-gray-700" role="status">
            <Sparkles className="mt-0.5 size-4 shrink-0 text-accent" aria-hidden="true" />
            <div className="space-y-0.5">
              <p>
                Filled <span className="font-medium text-gray-900">{result.count} field{result.count === 1 ? '' : 's'}</span>.
                Check the highlighted ones before saving.
              </p>
              {result.notes ? <p className="text-gray-500">Note from the AI: {result.notes}</p> : null}
              {!result.stored ? (
                <p className="flex items-center gap-1 text-gray-500">
                  <Info className="size-3.5" aria-hidden="true" />
                  The photo wasn't stored. Add an image URL for the product below.
                </p>
              ) : null}
            </div>
          </div>
        ) : null}

        <div className="flex items-center justify-between gap-3">
          <p className="text-xs text-gray-500">
            {enabled ? 'Price and barcode are never filled by AI.' : 'Fill the form manually for now.'}
          </p>
          <Button variant="primary" onClick={read} disabled={!canRead} loading={Boolean(step)}>
            {step ? null : <Sparkles className="size-4" />}
            {step === 'uploading' ? 'Uploading photo…' : step === 'reading' ? 'Reading pack…' : 'Read pack shot'}
          </Button>
        </div>
      </div>
    </section>
  )
}
