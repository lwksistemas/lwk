window.config = {
  routerBasename: '/',
  extensions: [],
  modes: [],
  showStudyList: true,
  maxNumberOfWebWorkers: 3,
  defaultDataSourceName: 'lwk',
  dataSources: [
    {
      namespace: '@ohif/extension-default.dataSourcesModule.dicomweb',
      sourceName: 'lwk',
      configuration: {
        friendlyName: 'LWK Orthanc',
        name: 'orthanc',
        // Em produção o browser deve apontar para o PROXY Django:
        // https://api.lwksistemas.com.br/api/radiologia/dicomweb/
        // Nunca expor Orthanc na internet sem autenticação de tenant.
        wadoUriRoot: 'http://127.0.0.1:8042/wado',
        qidoRoot: 'http://127.0.0.1:8042/dicom-web',
        wadoRoot: 'http://127.0.0.1:8042/dicom-web',
        qidoSupportsIncludeField: true,
        imageRendering: 'wadors',
        thumbnailRendering: 'wadors',
        enableStudyLazyLoad: true,
        supportsFuzzyMatching: true,
      },
    },
  ],
};
