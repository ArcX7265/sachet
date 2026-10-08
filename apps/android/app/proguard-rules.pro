# Workers are constructed by WorkManager through their retained public constructor.
-keep class in.sachet.app.UploadWorker { public <init>(...); }
