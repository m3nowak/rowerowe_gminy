{{/* Generate image name based on version if tag kept as not specified*/}}
{{- define "image" -}}
{{- default "ghcr.io/m3nowak/api" .Values.api.image.repository }}:{{ default .Chart.Version .Values.api.image.tag }}
{{- end -}}