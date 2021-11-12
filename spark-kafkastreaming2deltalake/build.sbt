name := "first_sbt"

version := "1.0"

/* assemblyOption in assembly := (assemblyOption in assembly).value.copy(includeScala = false)

assemblyMergeStrategy in assembly := {
  case PathList("org", "apache", "spark", "unused", "UnusedStubClass.class") => MergeStrategy.first
  case PathList(pl @ _*) if pl.contains("log4j.properties") => MergeStrategy.concat
  case PathList("META-INF", "io.netty.versions.properties") => MergeStrategy.last
  case x =>
    val oldStrategy = (assemblyMergeStrategy in assembly).value
    oldStrategy(x)
} */

fork in run := true
javaOptions in run ++= Seq(
  "-Dlog4j.debug=true",
  "-Dlog4j.configuration=log4j.properties")

scalaVersion := "2.12.10"

val sparkVersion = "3.1.2"

libraryDependencies ++= Seq(
  "org.apache.spark" %% "spark-core" % sparkVersion,
  "org.apache.spark" %% "spark-streaming" % sparkVersion,
  "org.apache.spark" %% "spark-sql" % sparkVersion,
  "org.apache.spark" %% "spark-streaming-kafka-0-10" % sparkVersion,
  "org.apache.kafka" %% "kafka" % "2.8.0",
  "org.apache.kafka" % "kafka-clients" % "2.8.0",
  "org.apache.spark" %% "spark-sql-kafka-0-10" % sparkVersion,
  "io.delta" %% "delta-core" % "1.0.0"
)
