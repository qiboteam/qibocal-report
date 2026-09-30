export function isQibocalMissing(protocols) {
  return (protocols || []).some(proto =>
    proto.error_code === 'qibocal_not_installed' ||
    /qibocal is not installed/i.test(proto.error || '')
  )
}

export function getPlotGenerationErrors(protocols) {
  return [...new Set((protocols || [])
    .filter(proto => proto.error || proto.status === 'error')
    .map(proto => proto.error || `Plot generation failed for ${proto.name || proto.id}.`))]
}
